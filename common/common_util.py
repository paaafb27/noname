# 📦 common_utils.py
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
)

def click_element(driver, xpath: str, timeout: int = 30) -> str:
    """
    지정한 XPath 요소를 클릭하는 공통 유틸 함수.
    성공 시 'success'를 반환하고,
    실패 시 상황에 맞는 에러 메시지를 문자열로 반환.
    """
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        ActionChains(driver).move_to_element(element).click().perform()
        return "success"

    except TimeoutException:
        return "Timeout: 요소를 찾지 못했습니다."

    except NoSuchElementException:
        return "NoSuchElement: XPath를 다시 확인하세요."

    except ElementClickInterceptedException:
        return "Intercepted: 다른 요소가 클릭을 가로막고 있습니다."

    except ElementNotInteractableException:
        return "NotInteractable: 요소가 클릭 가능한 상태가 아닙니다."

    except Exception as e:
        return f"UnknownError: {e}"
