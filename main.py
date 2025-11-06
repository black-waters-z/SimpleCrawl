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

browser_config = {
    "headless": False,
    "executablePath": r"C:\Program Files\Google\Chrome\Application\Chrome.exe",
    "args": ['--no-sandbox', '--disable-setuid-sandbox',
             '--disable-blink-features=AutomationControlled'],
    "ignoreDefaultArgs": ['--enable-automation']
}


class PypetterBrowser:
    def __init__(self, settings: dict):
        self.browser = None
        self.page = None
        self.config = settings

    async def init_browser(self):
        # 启动浏览器
        self.browser = await launch(**self.config)  # 可选参数
        self.page = await self.browser.newPage()
        return self.browser, self.page


class CsdnCrawl:
    def __init__(self,start_page_num:int,end_page_num:int):
        self.PypetterInit = PypetterBrowser(browser_config)
        self.browser = None
        self.page = None
        self.start=start_page_num
        self.end=end_page_num

    async def goto_page(self, page_href):
        try:
            await self.page.goto(page_href, {'timeout': 600000})

            h1_text = await self.page.evaluate('document.querySelector("h1").innerText')
            if h1_text.endswith(".docx" or ".doc" or ".pdf" or ".txt" or "pptx"):
                return

            baidu_pl_texts = await self.page.evaluate('''() => {
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
                data = [jianli_content]

            async with aiofiles.open("jianli.json", mode="w", encoding="utf-8") as f:
                await f.write(json.dumps(data, ensure_ascii=False, indent=4))

            print(f'{h1_text},{page_href}爬取完成')
        except Exception as e:
            pass
        finally:
            return

    def get_csdn_search_info(self, page_num: int):
        url = "https://so.csdn.net/api/v3/search"
        params = {
            "q": "简历技巧",
            "t": "all",
            "p": str(page_num),
        }
        response = session.get(url, headers=config.headers, cookies=config.cookies, params=params,
                               verify=certifi.where())

        if response.status_code == 200:
            response.encoding = "utf-8"
            results = response.json().get("result_vos")
            return results

    def get_page_href(self, result_dict: dict):
        return result_dict.get("url")

    async def main(self):
        self.browser, self.page = await self.PypetterInit.init_browser()
        try:
            for page_num in range(self.start, self.end+1):
                results = self.get_csdn_search_info(page_num)
                for result in results:
                    page_href = self.get_page_href(result)
                    await self.goto_page(page_href)
                    await asyncio.sleep(2)
        except Exception as e:
            print(e)
        finally:
            await self.browser.close()


if __name__ == '__main__':
    csdn_crawl = CsdnCrawl(1,5)
    asyncio.get_event_loop().run_until_complete(csdn_crawl.main())
