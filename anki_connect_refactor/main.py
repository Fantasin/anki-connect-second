import sys

from note_parser import add_audio_to_deck


def main():
    deck_name = input("Enter your Anki deck name to add audio to:\n").strip()

    if deck_name:
        try:
            add_audio_to_deck(deck_name)
            print(f"\nAudio successfully added to {deck_name}")
        except Exception as e:
            print(f"\n Deck name {e} is not valid")
            sys.exit(1)
    else:
        print("Deck name cannot be empty.")


if __name__ == "__main__":
    main()


