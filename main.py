# 这是一个示例 Python 脚本。

# 按 Shift+F10 执行或将其替换为您的代码。
# 按 双击 Shift 在所有地方搜索类、文件、工具窗口、操作和设置。
import json
import asyncio
import os

import aiofiles as aiofiles
from pyppeteer import launch
import requests
import certifi
import config

session = requests.session()


async def init_browser():
    # 启动浏览器
    browser = await launch(headless=False,  # 设置为 False 会显示浏览器界面，True 为无界面模式
                           executablePath="C:\Program Files\Google\Chrome\Application\Chrome.exe",
                           args=['--no-sandbox', '--disable-setuid-sandbox',
                                 '--disable-blink-features=AutomationControlled']
                           , ignoreDefaultArgs=['--enable-automation'])  # 可选参数
    page = await browser.newPage()
    return browser, page


async def goto_page(page_href, page):
    try:
        await page.goto(page_href, {'timeout': 600000})

        h1_text = await page.evaluate('document.querySelector("h1").innerText')
        if h1_text.endswith(".docx" or ".doc" or ".pdf" or ".txt" or "pptx"):
            return

        # Extract all text from elements with the 'baidu_pl' class
        baidu_pl_texts = await page.evaluate('''() => {
               const elements = document.querySelectorAll('.baidu_pl');
               return Array.from(elements).map(element => element.innerText);
           }''')

        baidu_pl_texts = "".join(" ".join(baidu_pl_texts).split())
        if not baidu_pl_texts:
            return

        jianli_content = {
            "title": h1_text,
            "content": baidu_pl_texts
        }

        if os.path.exists("jianli.json"):
            async with aiofiles.open("jianli.json", mode="r", encoding="utf-8") as f:
                file_content = await f.read()
                try:
                    data = json.loads(file_content)
                    if isinstance(data, list):
                        data.append(jianli_content)
                    else:
                        data = [data, jianli_content]
                except json.JSONDecodeError:
                    data = [jianli_content]
        else:
            # 如果文件不存在，直接创建一个包含该数据的新列表
            data = [jianli_content]

            # 将数据重新写入文件
        async with aiofiles.open("jianli.json", mode="w", encoding="utf-8") as f:
            # 将数据转换为 JSON 字符串并写入文件
            await f.write(json.dumps(data, ensure_ascii=False, indent=4))

        print(f'{h1_text},{page_href}爬取完成')
    except Exception as e:
        pass
    finally:
        return
        # 当你完成任务后，记得关闭浏览器
        # await browser.close()


def get_csdn_search_info(page_num: int):
    url = "https://so.csdn.net/api/v3/search"
    params = {
        "q": "简历技巧",
        "t": "all",
        "p": str(page_num),
    }
    response = session.get(url, headers=config.headers, cookies=config.cookies, params=params, verify=certifi.where())

    if response.status_code == 200:
        response.encoding = "utf-8"
        results = response.json().get("result_vos")
        return results


def get_page_href(result_dict: dict):
    return result_dict.get("url")


async def main():
    browser, page = await init_browser()
    try:
        for page_num in range(3, 5):
            results = get_csdn_search_info(page_num)
            for result in results:
                page_href = get_page_href(result)
                await goto_page(page_href, page)
                await asyncio.sleep(2)
    except Exception as e:
        print(e)
    finally:
        await browser.close()

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
