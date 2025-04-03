import customtkinter as ctk
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi
from pytube import extract
import threading
from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import tool, AgentExecutor, create_tool_calling_agent


class ASUStudyPartnerApp:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("ASU Study Partner")
        self.window.geometry("1200x800")

        # Theme settings
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.api_key = None
        self.model = None
        self.langchain_model = None
        self.agent_exec = None
        self.is_processing = False
        self.main_frame = None
        self.api_key_entry = None
        self.api_submit_btn = None
        self.input_entry = None
        self.submit_btn = None
        self.output_text =None
        self.status_label = None


        # Initialize LangChain prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant."),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])

        self.setup_ui()

    def setup_ui(self):
        # Main container
        self.main_frame = ctk.CTkFrame(self.window)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header_frame = ctk.CTkFrame(self.main_frame)
        header_frame.pack(fill="x", padx=10, pady=(0, 20))

        ctk.CTkLabel(
            header_frame,
            text="ASU Study Partner",
            font=("Alexandria-bold", 30)
        ).pack(pady=10)

        ctk.CTkLabel(
            header_frame,
            text="Contact: @mosa abdulaziz | 0122 586 2134",
            font=("Alexandria-bold", 14)
        ).pack()

        # API Key Section
        api_frame = ctk.CTkFrame(self.main_frame)
        api_frame.pack(fill="x", padx=10, pady=(0, 20))

        ctk.CTkLabel(
            api_frame,
            text="Google API Key:",
            font=("Arial", 14)
        ).pack(side="left", padx=5)

        self.api_key_entry = ctk.CTkEntry(
            api_frame,
            placeholder_text="Enter your API key",
            show="●",
            width=300
        )
        self.api_key_entry.pack(side="left", padx=5)

        self.api_submit_btn = ctk.CTkButton(
            api_frame,
            text="Submit API Key",
            command=self.submit_api
        )
        self.api_submit_btn.pack(side="left", padx=5)

        # Input Section
        input_frame = ctk.CTkFrame(self.main_frame)
        input_frame.pack(fill="x", padx=10, pady=(0, 20))

        ctk.CTkLabel(
            input_frame,
            text="Enter question or YouTube URL:",
            font=("Arial", 14)
        ).pack(side="left", padx=5)

        self.input_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Type your question or paste URL",
            width=300
        )
        self.input_entry.pack(side="left", padx=5)

        self.submit_btn = ctk.CTkButton(
            input_frame,
            text="Submit",
            command=self.process_input
        )
        self.submit_btn.pack(side="left", padx=5)

        # Output Section
        self.output_text = ctk.CTkTextbox(
            self.main_frame,
            wrap="word",
            font=("Alexandria-medium", 14)
        )
        self.output_text.pack(fill="both", expand=True, padx=10)

        # Status Bar
        self.status_label = ctk.CTkLabel(
            self.window,
            text="Ready",
            font=("Arial", 12)
        )
        self.status_label.pack(side="bottom", fill="x", padx=10, pady=5)

    def show_status(self, message, status_type="info"):
        colors = {
            "error": "red",
            "success": "green",
            "info": "white"
        }
        self.status_label.configure(
            text=message,
            text_color=colors.get(status_type, "white")
        )

    def setup_langchain_tools(self):
        @tool
        def request_from_text(request: str, text: str) -> str:
            """Process a given text based on the request given"""
            try:
                prompting = f"{request}:\n\n{text}"
                returned_text = self.langchain_model.invoke(prompting)
                return returned_text.content
            except Exception as en:
                return f"Error processing text: {str(en)}"

        @tool
        def request_from_url(request: str, url: str) -> str:
            """Process a YouTube video given its URL based on the request given"""
            try:
                id_ = extract.video_id(url)
                txt = YouTubeTranscriptApi.get_transcript(id_, ['ar', 'en'])
                whole_text = "".join(item['text'] for item in txt)
                prompting = f"{request}:\n\n{whole_text}"
                returned_text = self.langchain_model.invoke(prompting)
                return returned_text.content
            except Exception as es:
                return f"Error processing video: {str(es)}"

        tools = [request_from_url, request_from_text]

        try:
            agent = create_tool_calling_agent(self.langchain_model, tools, self.prompt)
            self.agent_exec = AgentExecutor(agent=agent, tools=tools, verbose=True)
        except Exception as e:
            raise Exception(f"Error creating agent: {str(e)}")

    def submit_api(self):
        api_key = self.api_key_entry.get().strip()
        if not api_key:
            self.show_status("Please enter an API key", "error")
            return

        try:
            # Configure Google AI
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-pro')

            # Configure LangChain
            self.langchain_model = ChatGoogleGenerativeAI(
                api_key=api_key,
                model="gemini-1.5-pro",
                temperature=0
            )

            # Setup LangChain tools and agent
            self.setup_langchain_tools()

            # Test the API key
            response = self.model.generate_content("Hello")
            if response:
                self.api_key = api_key
                self.api_key_entry.configure(state="disabled")
                self.api_submit_btn.configure(state="disabled")
                self.show_status("API Key validated successfully", "success")
            else:
                self.show_status("Invalid API key", "error")
        except Exception as e:
            self.show_status(f"Error: {str(e)}", "error")

    def process_input(self):
        if self.is_processing:
            return

        if not self.api_key or not self.model or not self.agent_exec:
            self.show_status("Please submit API key first", "error")
            return

        user_input = self.input_entry.get().strip()
        if not user_input:
            self.show_status("Please enter a question or URL", "error")
            return

        self.is_processing = True
        self.submit_btn.configure(state="disabled")
        self.show_status("Processing...", "info")

        def process_thread():
            try:
                # Use LangChain agent to process the input
                result = self.agent_exec.invoke({"input": user_input})

                self.window.after(0, lambda: [
                    self.output_text.insert("end", f"\nQ: {user_input}\n\nA: {result['output']}\n\n"),
                    self.output_text.see("end"),
                    self.show_status("Ready", "success"),
                    self.input_entry.delete(0, "end")
                ],)

            except Exception as e:
                self.window.after(0, lambda: self.show_status(f"Error: {str(e)}", "error"))

            finally:
                self.is_processing = False
                self.window.after(0, lambda: self.submit_btn.configure(state="normal"))

        threading.Thread(target=process_thread, daemon=True).start()

    def run(self):
        self.window.mainloop()


if __name__ == "__main__":
    app = ASUStudyPartnerApp()
    app.run()
