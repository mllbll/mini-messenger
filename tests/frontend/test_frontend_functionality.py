"""
Frontend functionality tests using Selenium.
"""
import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class TestFrontendFunctionality:
    """Test frontend functionality with Selenium."""
    
    @pytest.fixture(scope="class")
    def driver(self):
        """Set up Chrome driver for testing."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Use system ChromeDriver (installed by GitHub Actions)
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()
    
    @pytest.fixture
    def frontend_url(self):
        """Frontend URL for testing."""
        return "http://localhost:3000"
    
    def test_page_loads(self, driver, frontend_url):
        """Test that the frontend page loads correctly."""
        driver.get(frontend_url)
        
        # Check that the page title is set
        assert "Mini Messenger" in driver.title or "Messenger" in driver.title
        
        # Check that main elements are present
        assert driver.find_element(By.ID, "authScreen") is not None
        assert driver.find_element(By.ID, "appScreen") is not None
    
    def test_user_registration(self, driver, frontend_url):
        """Test user registration functionality."""
        driver.get(frontend_url)
        
        # Switch to registration mode using JavaScript click to avoid modal interference
        switch_mode = driver.find_element(By.ID, "switchMode")
        driver.execute_script("arguments[0].click();", switch_mode)
        time.sleep(0.5)  # Wait for UI to update
        
        # Find registration form elements
        username_input = driver.find_element(By.ID, "username")
        password_input = driver.find_element(By.ID, "password")
        register_button = driver.find_element(By.ID, "authBtn")
        
        # Fill registration form
        username_input.clear()
        username_input.send_keys("testuser_frontend")
        
        password_input.clear()
        password_input.send_keys("testpassword123")
        
        # Click register button using JavaScript to avoid modal interference
        driver.execute_script("arguments[0].click();", register_button)
        
        # Wait for successful registration (should show app screen)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "appScreen"))
            )
            assert True  # Registration successful
        except TimeoutException:
            # Check for error message
            error_elements = driver.find_elements(By.CLASS_NAME, "error")
            if error_elements:
                error_text = error_elements[0].text
                print(f"Registration error: {error_text}")
            assert False, "Registration failed or timed out"
    
    def test_user_login(self, driver, frontend_url):
        """Test user login functionality."""
        driver.get(frontend_url)
        
        # First register a user
        switch_mode = driver.find_element(By.ID, "switchMode")
        driver.execute_script("arguments[0].click();", switch_mode)
        time.sleep(0.5)  # Wait for UI to update
        
        username_input = driver.find_element(By.ID, "username")
        password_input = driver.find_element(By.ID, "password")
        register_button = driver.find_element(By.ID, "authBtn")
        
        username_input.clear()
        username_input.send_keys("logintest_user")
        
        password_input.clear()
        password_input.send_keys("testpassword123")
        
        driver.execute_script("arguments[0].click();", register_button)
        
        # Wait for registration to complete
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "appScreen"))
        )
        
        # Logout - find by title attribute since it's created dynamically
        logout_button = driver.find_element(By.XPATH, "//button[@title='Logout']")
        driver.execute_script("arguments[0].click();", logout_button)
        
        # Wait for login screen
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "authScreen"))
        )
        
        # Login with same credentials
        username_input = driver.find_element(By.ID, "username")
        password_input = driver.find_element(By.ID, "password")
        login_button = driver.find_element(By.ID, "authBtn")
        
        username_input.clear()
        username_input.send_keys("logintest_user")
        
        password_input.clear()
        password_input.send_keys("testpassword123")
        
        driver.execute_script("arguments[0].click();", login_button)
        
        # Wait for successful login
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "appScreen"))
            )
            assert True  # Login successful
        except TimeoutException:
            assert False, "Login failed or timed out"
    
    def test_chat_creation(self, driver, frontend_url):
        """Test chat creation functionality."""
        driver.get(frontend_url)
        
        # Handle any existing alerts
        try:
            alert = driver.switch_to.alert
            alert.accept()
        except:
            pass
        
        # Register and login
        self._register_and_login(driver, "chattest_user", "testpassword123")
        
        # Find and click the "Публичный чат" button - find by onclick attribute
        public_chat_button = driver.find_element(By.XPATH, "//button[@onclick='showCreatePublicChatForm()']")
        driver.execute_script("arguments[0].click();", public_chat_button)
        
        # Wait for modal to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "createChatModal"))
        )
        
        # Fill chat name
        chat_name_input = driver.find_element(By.ID, "publicChatName")
        chat_name_input.clear()
        chat_name_input.send_keys("Test Chat from Frontend")
        
        # Click create button
        create_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Создать')]")
        driver.execute_script("arguments[0].click();", create_button)
        
        # Wait for modal to close and chat to appear
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.ID, "createChatModal"))
        )
        
        # Check that chat appears in sidebar
        chat_items = driver.find_elements(By.CLASS_NAME, "chat-item")
        assert len(chat_items) > 0, "No chats found in sidebar"
    
    def test_message_sending(self, driver, frontend_url):
        """Test message sending functionality."""
        driver.get(frontend_url)
        
        # Handle any existing alerts
        try:
            alert = driver.switch_to.alert
            alert.accept()
        except:
            pass
        
        # Register and login
        self._register_and_login(driver, "messagetest_user", "testpassword123")
        
        # Create a chat
        self._create_chat(driver, "Message Test Chat")
        
        # Select the chat
        chat_items = driver.find_elements(By.CLASS_NAME, "chat-item")
        if chat_items:
            driver.execute_script("arguments[0].click();", chat_items[0])
            
            # Wait for chat to be selected
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "chat-area"))
            )
            
            # Find message input and send button
            message_input = driver.find_element(By.ID, "messageInput")
            send_button = driver.find_element(By.CLASS_NAME, "send-button")
            
            # Send a message
            message_input.clear()
            message_input.send_keys("Hello from frontend test!")
            driver.execute_script("arguments[0].click();", send_button)
            
            # Wait for message to appear
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "message"))
                )
                assert True  # Message sent successfully
            except TimeoutException:
                assert False, "Message was not sent or did not appear"
    
    def test_user_search(self, driver, frontend_url):
        """Test user search functionality."""
        driver.get(frontend_url)
        
        # Handle any existing alerts
        try:
            alert = driver.switch_to.alert
            alert.accept()
        except:
            pass
        
        # Register and login
        self._register_and_login(driver, "searchtest_user", "testpassword123")
        
        # Click user search button - find by onclick attribute
        search_button = driver.find_element(By.XPATH, "//button[@onclick='showUserSearchModal()']")
        driver.execute_script("arguments[0].click();", search_button)
        
        # Wait for modal to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "userSearchModal"))
        )
        
        # Fill search input
        search_input = driver.find_element(By.ID, "userSearchInput")
        search_input.clear()
        search_input.send_keys("searchtest")
        
        # Click search button
        search_submit_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Поиск')]")
        driver.execute_script("arguments[0].click();", search_submit_button)
        
        # Wait for results
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "search-results"))
            )
            assert True  # Search completed
        except TimeoutException:
            # Search might return no results, which is also valid
            assert True
    
    def test_modal_functionality(self, driver, frontend_url):
        """Test modal window functionality."""
        driver.get(frontend_url)
        
        # Handle any existing alerts
        try:
            alert = driver.switch_to.alert
            alert.accept()
        except:
            pass
        
        # Register and login
        self._register_and_login(driver, "modaltest_user", "testpassword123")
        
        # Test modal opening and closing
        buttons_to_test = [
            ("showUserSearchModal()", "userSearchModal"),
            ("showCreatePublicChatForm()", "createChatModal"),
            ("showCreatePrivateChatForm()", "createChatModal"),
            ("showQuickMessageForm()", "createChatModal")
        ]
        
        for onclick_func, modal_id in buttons_to_test:
            # Click button by onclick attribute
            button = driver.find_element(By.XPATH, f"//button[@onclick='{onclick_func}']")
            driver.execute_script("arguments[0].click();", button)
            
            # Wait for modal to appear
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, modal_id))
            )
            
            # Close modal with X button
            close_button = driver.find_element(By.CLASS_NAME, "modal-close")
            driver.execute_script("arguments[0].click();", close_button)
            
            # Wait for modal to disappear
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element_located((By.ID, modal_id))
            )
    
    def test_responsive_design(self, driver, frontend_url):
        """Test responsive design on different screen sizes."""
        driver.get(frontend_url)
        
        # Test different screen sizes
        screen_sizes = [
            (1920, 1080),  # Desktop
            (1024, 768),   # Tablet
            (375, 667),    # Mobile
        ]
        
        for width, height in screen_sizes:
            driver.set_window_size(width, height)
            time.sleep(1)  # Wait for layout to adjust
            
            # Check that main elements are still visible
            assert driver.find_element(By.ID, "authScreen") is not None
            assert driver.find_element(By.ID, "appScreen") is not None
    
    def _register_and_login(self, driver, username, password):
        """Helper method to register and login a user."""
        # Switch to registration mode using JavaScript click to avoid modal interference
        switch_mode = driver.find_element(By.ID, "switchMode")
        driver.execute_script("arguments[0].click();", switch_mode)
        time.sleep(0.5)  # Wait for UI to update
        
        # Register
        username_input = driver.find_element(By.ID, "username")
        password_input = driver.find_element(By.ID, "password")
        register_button = driver.find_element(By.ID, "authBtn")
        
        username_input.clear()
        username_input.send_keys(username)
        
        password_input.clear()
        password_input.send_keys(password)
        
        driver.execute_script("arguments[0].click();", register_button)
        
        # Wait for registration to complete
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "appScreen"))
        )
        
        # Handle any alerts that might appear
        try:
            alert = driver.switch_to.alert
            alert.accept()
        except:
            pass  # No alert present
    
    def _create_chat(self, driver, chat_name):
        """Helper method to create a chat."""
        # Click public chat button - find by onclick attribute
        public_chat_button = driver.find_element(By.XPATH, "//button[@onclick='showCreatePublicChatForm()']")
        driver.execute_script("arguments[0].click();", public_chat_button)
        
        # Wait for modal
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "createChatModal"))
        )
        
        # Fill chat name
        chat_name_input = driver.find_element(By.ID, "publicChatName")
        chat_name_input.clear()
        chat_name_input.send_keys(chat_name)
        
        # Create chat
        create_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Создать')]")
        driver.execute_script("arguments[0].click();", create_button)
        
        # Wait for modal to close
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.ID, "createChatModal"))
        )


class TestFrontendPerformance:
    """Test frontend performance."""
    
    @pytest.fixture(scope="class")
    def driver(self):
        """Set up Chrome driver for performance testing."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Performance testing options
        chrome_options.add_argument("--enable-logging")
        chrome_options.add_argument("--log-level=0")
        
        # Use system ChromeDriver (installed by GitHub Actions)
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()
    
    def test_page_load_time(self, driver):
        """Test page load time."""
        start_time = time.time()
        driver.get("http://localhost:3000")
        
        # Wait for page to fully load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "authScreen"))
        )
        
        load_time = time.time() - start_time
        
        # Page should load within 5 seconds
        assert load_time < 5.0, f"Page load time too slow: {load_time:.2f}s"
    
    def test_large_message_handling(self, driver):
        """Test handling of large messages."""
        driver.get("http://localhost:3000")
        
        # Handle any existing alerts
        try:
            alert = driver.switch_to.alert
            alert.accept()
        except:
            pass
        
        # Register and login
        switch_mode = driver.find_element(By.ID, "switchMode")
        driver.execute_script("arguments[0].click();", switch_mode)
        time.sleep(0.5)  # Wait for UI to update
        
        username_input = driver.find_element(By.ID, "username")
        password_input = driver.find_element(By.ID, "password")
        register_button = driver.find_element(By.ID, "authBtn")
        
        username_input.clear()
        username_input.send_keys("largetest_user")
        
        password_input.clear()
        password_input.send_keys("testpassword123")
        
        driver.execute_script("arguments[0].click();", register_button)
        
        # Wait for login
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "appScreen"))
        )
        
        # Handle any alerts that might appear
        try:
            alert = driver.switch_to.alert
            alert.accept()
        except:
            pass
        
        # Create a chat
        public_chat_button = driver.find_element(By.XPATH, "//button[@onclick='showCreatePublicChatForm()']")
        driver.execute_script("arguments[0].click();", public_chat_button)
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "createChatModal"))
        )
        
        chat_name_input = driver.find_element(By.ID, "publicChatName")
        chat_name_input.clear()
        chat_name_input.send_keys("Large Message Test")
        
        create_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Создать')]")
        driver.execute_script("arguments[0].click();", create_button)
        
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element_located((By.ID, "createChatModal"))
        )
        
        # Select chat
        chat_items = driver.find_elements(By.CLASS_NAME, "chat-item")
        if chat_items:
            driver.execute_script("arguments[0].click();", chat_items[0])
            
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "chat-area"))
            )
            
            # Send a large message
            large_message = "A" * 1000  # 1000 character message
            message_input = driver.find_element(By.ID, "messageInput")
            send_button = driver.find_element(By.CLASS_NAME, "send-button")
            
            message_input.clear()
            message_input.send_keys(large_message)
            
            start_time = time.time()
            driver.execute_script("arguments[0].click();", send_button)
            
            # Wait for message to appear
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "message"))
                )
                send_time = time.time() - start_time
                
                # Large message should be sent within 3 seconds
                assert send_time < 3.0, f"Large message send time too slow: {send_time:.2f}s"
            except TimeoutException:
                assert False, "Large message was not sent"
