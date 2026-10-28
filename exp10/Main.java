import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;

public class Main {
    public static void main(String[] args) {
        System.out.println("Starting Selenium WebDriver in Java...");
        
        // Initialize ChromeDriver (Selenium 4 manages drivers automatically)
        WebDriver driver = new ChromeDriver();
        
        try {
            // Open Google
            driver.get("https://www.google.com");
            
            // Print page title
            System.out.println("Page Title is: " + driver.getTitle());
            
            // Keep browser open for 5 seconds to see it live
            Thread.sleep(5000);
        } catch (InterruptedException e) {
            e.printStackTrace();
        } finally {
            // Close browser
            driver.quit();
            System.out.println("Browser closed successfully.");
        }
    }
}