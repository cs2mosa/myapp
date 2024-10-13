import streamlit as st
import youtube_transcript_api
from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from youtube_transcript_api import YouTubeTranscriptApi
from pytube import extract

st.set_page_config(page_title="ASU study partner", page_icon="🎥")

st.title("ASU study partner is here for you!")
st.subheader("AI-powered chatbot to process YouTube videos and texts")
st.text("powered by gemini pro")

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

api_key = st.text_input("Enter your Google API key:", type="password")
if api_key:
    model = ChatGoogleGenerativeAI(
        api_key=api_key,
        model="gemini-1.5-pro",
        temperature=0
    )


    @tool
    def request_from_text(request:str,text: str) -> str:
        """process a given based on the request given
                    :parameter request : the user request
                    :parameter text: text to process
                    :returns the processed text tailored to user's need"""
        try:
            prompting = f"as an expert in undergraduate courses,{request}: here is the text: \n\n{text}"
            returned_text = model.invoke(prompting)
            return returned_text.content
        except Exception:
            st.error("Error generating summary")
            return "Unable to get a summary of this video due to an error. Please try another one."


    @tool
    def request_from_url(request:str,url: str) -> str:
        """process a YouTube video given its URL based on the request given
            :parameter request : the user request
            :parameter url: the YouTube video url
            :returns the processed text tailored to user's need"""

        try:
            id_ = extract.video_id(url)
        except Exception:
            st.error(f"Error extracting video ID")
            return "Not a valid YouTube video. Please use another link."

        try:
            txt = YouTubeTranscriptApi.get_transcript(id_, ['ar', 'en'])
        except youtube_transcript_api.NoTranscriptFound:
            st.warning("No transcript found for video ID, please refer to this website to get a transcription then ask another prompt, link: https://tactiq.io/tools/youtube-transcript ")
            return "Error: Please try another video."
        except Exception:
            st.error("Error fetching text, please refer to this website to get a transcription then ask another prompt, link: https://tactiq.io/tools/youtube-transcript , or use any other transcript service")
            return "Error: Unable to fetch video transcript."

        whole_text = "".join(item['text'] for item in txt)

        try:
            prompting = f"{request}:\n\n{whole_text}"
            returned_text = model.invoke(prompting)
            return returned_text.content
        except Exception:
            st.error(f"Error generating summary")
            return "Unable to get a summary of this video due to an error. Please try another one."

    tools = [request_from_url,request_from_text]

    try:
        agent = create_tool_calling_agent(model, tools, prompt)
        agent_exec = AgentExecutor(agent=agent, tools=tools, verbose=True)
    except Exception:
        st.error(f"Error creating agent")
        st.stop()

    st.subheader("Ask a question or request a video/text summary")
    user_input = st.text_input("Enter your question with the YouTube URL:")

    if st.button("Submit"):
        if user_input:
            try:
                with st.spinner("Processing your request..."):
                    result = agent_exec.invoke({"input": user_input})
                st.write(result['output'])
            except Exception:
                st.error(f"An error occurred while processing your request")
        else:
            st.warning("Please enter a question or YouTube URL.")
else:
    st.warning("Please enter your Google API key to use the app.")