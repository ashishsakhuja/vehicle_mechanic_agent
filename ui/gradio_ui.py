import gradio as gr
from auto_mechanic_agent2.main import run


def query_agent(user_query):
    try:
        result = run(user_query)
        return result
    except Exception as e:
        return f"❌ Error: {str(e)}"


with gr.Blocks(css="""
    .logo-container {
        display: flex;
        align-items: center;
        padding: 10px;
    }

    .logo-container img {
        height: 40px;
        margin-right: 12px;
    }

    .logo-title {
        font-size: 22px;
        font-weight: bold;
        color: #ffd700;
    }

    body, .gradio-container {
        background-color: #1e1e1e;
        font-family: 'Segoe UI', sans-serif;
        color: #ffffff;
    }
""") as demo:
    with gr.Row():
        gr.HTML("""
            <div class="logo-container">
                <img src="file/logo.png" alt="Logo">
                <span class="logo-title">Auto Mechanic AI Assistant</span>
            </div>
        """)

    gr.Markdown("Enter your car issue and get help from the AI mechanic.")

    input_box = gr.Textbox(lines=3, label="Describe Your Car Problem")
    output_box = gr.Textbox(label="Agent's Diagnosis")
    run_button = gr.Button("Submit")

    run_button.click(query_agent, inputs=input_box, outputs=output_box)

if __name__ == "__main__":
    demo.launch()
