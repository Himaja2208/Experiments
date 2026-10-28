import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import java.io.File;

public class Main {
    public static void main(String[] args) {
        System.out.println("Starting Selenium JavaScript Counter Test...");

        // Initialize ChromeDriver
        WebDriver driver = new ChromeDriver();

        try {
            // Get absolute path of local index.html file
            File htmlFile = new File("index.html");
            String filePath = htmlFile.getAbsolutePath();

            // Open the local web page
            driver.get("file:///" + filePath);

            // Find the increment button and click it
            WebElement button = driver.findElement(By.id("increment-button"));
            button.click();

            // Get the text from output element
            WebElement output = driver.findElement(By.id("output"));
            String result = output.getText();

            // Check if test passed
            if ("1".equals(result)) {
                System.out.println("TEST PASSED: Button clicked successfully, count updated to 1!");
            } else {
                System.out.println("TEST FAILED: Expected 1, but found: " + result);
            }

            // Keep browser open for 3 seconds to capture live output
            Thread.sleep(3000);

        } catch (Exception e) {
            e.printStackTrace();
        } finally {
            // Close browser session
            driver.quit();
            System.out.println("Browser closed successfully.");
        }
    }
}