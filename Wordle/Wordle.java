package Wordle;

import java.util.Scanner;

public class Wordle {
    private String secretWord;
    private int attempts;
    public String guess = "";

    public Wordle(String secretWord, int attempts) {
        this.secretWord = secretWord;
        this.attempts = attempts;
        //this.guess = "";
    }

    public void play() {
        while (attempts > 0) {
            String guess;
            Scanner scanner1 = new Scanner(System.in);
            System.out.print("guess one language name: ");
            guess = scanner1.nextLine().toUpperCase();
            attempts --;

            if (guess.length() != secretWord.length()) {
                System.out.println(secretWord.length() + " letters only.");
                continue;
            }

            if (guess.equals(secretWord)) {
                attempts = 0;
                System.out.println("You've got it, it's " + secretWord);
            }
            if (attempts <= 0) {
                System.out.println("bye! The word was " + secretWord);
            }

            for (int i = 0; i < guess.length(); i++) {
                if (guess.charAt(i) == secretWord.charAt(i)) {
                    System.out.println(guess.charAt(i) + " is correct");
                } else if (secretWord.contains(Character.toString(guess.charAt(i)))) {
                    System.out.println(guess.charAt(i) + " is right but different position");
                } else {
                    System.out.println(guess.charAt(i) + " not in the word.");
                }
            }
        }
    }
}
