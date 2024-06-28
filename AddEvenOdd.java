package OCA;


import java.util.InputMismatchException;
import java.util.Scanner;

/** take an integer argument, and use recursion to add up the add or even number along the way to the int. */
public class Land11 {
    public static void main(String[] args) {
        //prompt user for an int.
        Scanner scanner1 = new Scanner(System.in);
        System.out.println("plz enter an positive integer: ");

        // try to convert user input to int, if not valid input, throws exception and print warning message.
        try {
            // if successfully convert to int, then check if it's greater than zero,
            int input = scanner1.nextInt();
            // execute adding operation and print result.
            if (input > 0) {
                System.out.println(addingDown(input));
                System.out.println(add(input));
            }
        } catch (InputMismatchException e) {
            System.out.println(e.getMessage());
            System.out.println("positive integer only.");
        }
    }
    // method that adding up from the input down to 1 or 2, adding down every other integer along the way.
    static int addingDown(int i) {
        if (i == 1) {
            return 1;
        } if (i == 2) {
            return 2;
        }
        else {
            return (i + addingDown(i - 2));
        }
    }

    static int add(int j) {
        int sum = 0;
        while (j > 0) {
            sum += j;
            j -= 2;
        }
        return sum;
    }
}
