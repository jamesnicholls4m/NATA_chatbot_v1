import streamlit as st
import pandas as pd
import openai

# Show title and description.
st.title("💬 Chatbot with File Upload")
st.write(
    "This is a simple chatbot that uses OpenAI's GPT-4 model to generate responses. "
    "To use this app, you need to provide an OpenAI API key, which you can get [here](https://platform.openai.com/account/api-keys). "
    "You can also learn how to build this app step by step by [following our tutorial](https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps)."
)

# Ask user for their OpenAI API key via `st.text_input`.
openai_api_key = st.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
else:
    # Set OpenAI API key.
    openai.api_key = openai_api_key

    # File uploader to allow users to upload an Excel or CSV file.
    uploaded_file = st.file_uploader("Upload an Excel or CSV file", type=["xlsx", "csv"])

    if uploaded_file:
        try:
            # Load the file into a DataFrame.
            if uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            elif uploaded_file.name.endswith('.csv'):
                # Try multiple encodings
                try:
                    df = pd.read_csv(uploaded_file, encoding='utf-8')
                except UnicodeDecodeError:
                    df = pd.read_csv(uploaded_file, encoding='latin1')
            
            st.write("File uploaded successfully. Data preview:")
            st.dataframe(df.head())
            
            # Function to search the DataFrame for an answer based on a question.
            def search_dataframe(question, dataframe):
                # Simple search: looks for the question text within each cell.
                results = dataframe.apply(lambda row: row.astype(str).str.contains(question, case=False).any(), axis=1)
                filtered_df = dataframe[results]
                return filtered_df

            # Create a session state variable to store the chat messages. This ensures that the
            # messages persist across reruns.
            if "messages" not in st.session_state:
                st.session_state.messages = []

            # Display the existing chat messages via `st.chat_message`.
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # Create a chat input field to allow the user to enter a message. This will display
            # automatically at the bottom of the page.
            if prompt := st.chat_input("What do you want to know from the uploaded file?"):

                # Store and display the current prompt.
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                # Search the DataFrame for the most appropriate answer.
                search_result = search_dataframe(prompt, df)
                search_result_text = search_result.to_string(index=False) if not search_result.empty else "No relevant information found in the file."

                # Display the search result
                st.write("Search Results:")
                st.dataframe(search_result)

                # Generate a response incorporating the search result.
                response_prompt = f"The user asked: {prompt}\n\nRelevant information from the file:\n{search_result_text}\n\nGenerate a response based on this information."

                # Generate the response using OpenAI's GPT-4 model.
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ] + [{"role": "assistant", "content": response_prompt}],
                    stream=True,
                )

                # Stream the response to the chat using `st.write_stream`, then store it in
                # session state.
                response_content = ""
                with st.chat_message("assistant"):
                    for chunk in response:
                        chunk_message = chunk["choices"][0].get("delta", {}).get("content", "")
                        response_content += chunk_message
                        st.markdown(chunk_message)
                st.session_state.messages.append({"role": "assistant", "content": response_content})

        except UnicodeDecodeError as e:
            st.error(f"Error: The file could not be read due to encoding issues. Please upload a file with compatible encoding.\n\n{str(e)}")
        except Exception as e:
            st.error(f"Error: {str(e)}")
