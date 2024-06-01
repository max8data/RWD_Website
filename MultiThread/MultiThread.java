import java.util.InputMismatchException;
import java.util.Scanner;

public class MultiThread {
    public static void main(String[] args) throws Exception {
        Scanner scanner1 = new Scanner(System.in);
        while (true) {
            System.out.println("what do you wanna check? ");
            try {
                int input = scanner1.nextInt();
                QueryThread thread1 = new QueryThread(input);
                thread1.start();
                thread1.join();
            } catch (InputMismatchException e) {
                System.out.println("plz enter an integer. ");
                scanner1.next();
            }

        }
    }
}

class QueryThread extends Thread {
    private final int number;
    private final int[] id = new int[]{1, 2, 3};
    private final int[] price = new int[]{18, 24, 36};
    public QueryThread(int number) {
        this.number = number;
    }

    @Override
    public void run() {
        for (int i = 0; i < id.length; i++) {
            if (id[i] == number) {
                System.out.println("the price for item " + (i + 1) + " is " + price[i] + " dollars.");
                return;
            }
        }
        System.out.println("can't find the id.");
    }
}
