package Wordle;

public class WordleGame {
    public static void main(String[] args) {
        String word = "java";
        int tries = 5;
        Wordle wordle1 = new Wordle(word.toUpperCase(), tries);
        wordle1.play();
    }
}
