from youtube_transcript_api import YouTubeTranscriptApi
from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from pytube import extract
import youtube_transcript_api

class YouTubeProcessor:
    def __init__(self, api_key):
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant."),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])

        self.model = ChatGoogleGenerativeAI(
            api_key=api_key,
            model="gemini-1.5-pro",
            temperature=0
        )

        self.setup_tools()

    def setup_tools(self):
        @tool
        def request_from_text(request: str, text: str) -> str:
            """Process a given text based on the request given
            :parameter request: the user request
            :parameter text: text to process
            :returns: the processed text tailored to user's need"""
            try:
                prompting = f"{request}:\n\n{text}"
                returned_text = self.model.invoke(prompting)
                return returned_text.content
            except Exception as e:
                print(f"Error generating summary: {str(e)}")
                return "Unable to process this text due to an error. Please try another one."

        @tool
        def request_from_url(request: str, url: str) -> str:
            """Process a YouTube video given its URL based on the request given
            :parameter request: the user request
            :parameter url: the YouTube video url
            :returns: the processed text tailored to user's need"""
            try:
                id_ = extract.video_id(url)
            except Exception as e:
                print(f"Error extracting video ID: {str(e)}")
                return "Not a valid YouTube video. Please use another link."

            try:
                txt = YouTubeTranscriptApi.get_transcript(id_, ['ar', 'en'])
            except youtube_transcript_api.NoTranscriptFound:
                print("No transcript found for video")
                return "Error: No transcript found. Please try another video or use a transcript service like https://tactiq.io/tools/youtube-transcript"
            except Exception as e:
                print(f"Error fetching transcript: {str(e)}")
                return "Error: Unable to fetch video transcript."

            whole_text = "".join(item['text'] for item in txt)

            try:
                prompting = f"{request}:\n\n{whole_text}"
                returned_text = self.model.invoke(prompting)
                return returned_text.content
            except Exception as e:
                print(f"Error processing video content: {str(e)}")
                return "Unable to process this video due to an error. Please try another one."

        self.tools = [request_from_url, request_from_text]

        try:
            self.agent = create_tool_calling_agent(self.model, self.tools, self.prompt)
            self.agent_exec = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True)
        except Exception as e:
            print(f"Error creating agent: {str(e)}")
            raise

    def process_request(self, user_input: str) -> str:
        """Process a user request
        :parameter user_input: the user's question/request with URL if applicable
        :returns: the processed response"""
        try:
            result = self.agent_exec.invoke({"input": user_input})
            return result['output']
        except Exception as e:
            print(f"Error processing request: {str(e)}")
            return "An error occurred while processing your request. Please check your API key or try again later."


def main():
    # Example usage
    api_key = input("Enter your Google API key: ")
    processor = YouTubeProcessor(api_key)

    while True:
        user_input = input("\nEnter your question with the YouTube URL (or 'quit' to exit): ")
        if user_input.lower() == 'quit':
            break

        if user_input:
            result = processor.process_request(user_input)
            print("\nResult:", result)
        else:
            print("Please enter a question or YouTube URL.")


if __name__ == "__main__":
    main()
