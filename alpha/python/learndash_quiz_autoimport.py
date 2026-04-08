from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, UnexpectedAlertPresentException, NoAlertPresentException
import os
import time

# Automate XML import via DOM form interaction with progress logging

def import_xml_files(source_dir, driver):
    # Gather XML files and compute total
    xml_files = [f for f in os.listdir(source_dir) if f.lower().endswith('.xml')]
    total = len(xml_files)
    if total == 0:
        print("No XML files found in directory:", source_dir)
        return

    print(f"Found {total} XML files. Beginning import...")
    base_url = "https://learningacademy.com/wp-admin/admin.php?page=ldAdvQuiz"
    wait = WebDriverWait(driver, 30)

    for index, filename in enumerate(xml_files, start=1):
        file_path = os.path.join(source_dir, filename)
        # Log progress
        print(f"[{index}/{total}] Importing: {filename}")

        # 1. Navigate to import page
        driver.get(base_url)

        # 2. Reveal the import section
        import_btn = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.wpProQuiz_import.button-secondary"))
        )
        driver.execute_script("arguments[0].click();", import_btn)

        # 3. Populate file input inside importList
        file_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.wpProQuiz_importList input[type='file']"))
        )
        file_input.send_keys(file_path)
        driver.execute_script(
            "arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
            file_input
        )

        # 4. Wait for file selection to register
        try:
            wait.until(lambda d: file_input.get_attribute("value") not in (None, ""))
        except TimeoutException:
            print(f"Error: File selection not detected for {filename}")
            continue
        time.sleep(1)

        # 5. Submit the import form directly
        driver.execute_script(
            "document.querySelector('div.wpProQuiz_importList form').submit();"
        )

        # 6. Wait for navigation to actual import page
        try:
            wait.until(EC.url_contains("module=importExport&action=import"))
        except TimeoutException:
            print(f"Error: Navigation to import page failed for {filename}")
            continue

        # 7. Click the second 'Start import'
        try:
            save_btn = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "div.wpProQuiz_importOverall input[name='importSave']"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true); arguments[0].click();", save_btn)
        except TimeoutException:
            print(f"Error: Second Start import button not clickable for {filename}")
            continue

        # 8. Wait for completion (button disappears)
        try:
            wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, "div.wpProQuiz_importOverall input[name='importSave']")))
            print(f"[{index}/{total}] Completed: {filename}")
        except TimeoutException:
            print(f"Warning: Final import not confirmed for {filename}")

        # Brief pause before next iteration
        time.sleep(1)


def main():
    source_dir = r"C:\\Users\\BenjaminLee\\LearnKey, Inc\\Development - Documents\\LMS\\Quizzes\\Ben generated XML"

    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)

    driver = webdriver.Chrome(options=options)

    # Manual login step
    driver.get("https://learningacademy.com/wp-admin/admin.php?page=ldAdvQuiz")
    print("Please sign in to WordPress (up to 5 minutes)...")
    WebDriverWait(driver, 300).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "a.wpProQuiz_import.button-secondary"))
    )
    print("Login detected. Starting imports...")

    try:
        import_xml_files(source_dir, driver)
    except UnexpectedAlertPresentException as e:
        print(f"Unexpected alert during import: {e.alert_text}")
    finally:
        print("Done. Chrome remains open for review.")

if __name__ == "__main__":
    main()
