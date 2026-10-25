


import os
from google import genai

def main():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("Please set your GEMINI_API_KEY environment variable.")
        return

    client = genai.Client(api_key=api_key)

    print("PixelTTV AI Agent is online!")
    print("Your Fortnite creator co-pilot is ready.")

    while True:
        question = input("\nYou: ").strip()

        if question.lower() in ["exit", "quit"]:
            print("PixelTTV AI Agent signing off!")
            break

        if not question:
            continue

        try:
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=question
            )
            print("\nPixelTTV AI:", response.text)
        except Exception as error:
            print("Something went wrong:", error)

if __name__ == "__main__":
    main()

