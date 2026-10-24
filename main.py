
import os

def main():
    print("Welcome to the PixelTTV AI Agent!")
    print("YouTube API setup: Ready")
    
    if os.path.exists("client_secret.json"):
        print("OAuth file found.")
        print("Next: authorize your YouTube account.")
    else:
        print("OAuth file not found yet.")
        print("Keep your downloaded Google JSON file private.")
        print("We will configure it securely next.")

if __name__ == "__main__":
    main()


