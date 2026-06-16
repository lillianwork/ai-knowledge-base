"""CDP utilities for Feishu wiki extraction."""
import websocket, json, time, urllib.request, io, sys, os

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class CDPClient:
    def __init__(self, tab_url_filter='feishu.cn'):
        req = urllib.request.Request('http://127.0.0.1:9222/json/list')
        resp = urllib.request.urlopen(req)
        tabs = json.loads(resp.read())
        page_tabs = [t for t in tabs if tab_url_filter in t.get('url', '') and t['type'] == 'page']
        if not page_tabs:
            raise RuntimeError(f'No tab found matching filter: {tab_url_filter}')
        self.tab = page_tabs[0]
        self.ws = websocket.create_connection(self.tab['webSocketDebuggerUrl'])
        self._mid = 0
        self._events = []

    def send(self, method, params=None):
        self._mid += 1
        msg = json.dumps({'id': self._mid, 'method': method, 'params': params or {}})
        self.ws.send(msg)
        return self._mid

    def recv_result(self, msg_id, timeout=15):
        start = time.time()
        buf = ''
        while time.time() - start < timeout:
            self.ws.settimeout(3.0)
            try:
                buf += self.ws.recv()
            except:
                continue
            try:
                r = json.loads(buf)
                if 'id' in r and r['id'] == msg_id:
                    if 'result' in r:
                        return r['result']
                    if 'error' in r:
                        return {'error': r['error']}
                # Save events
                if 'method' in r:
                    self._events.append(r)
                buf = ''
            except:
                pass
        return None

    def navigate(self, url, wait=6):
        nid = self.send('Page.navigate', {'url': url})
        self.recv_result(nid, 15)
        time.sleep(wait)

    def evaluate(self, expression, timeout=10, await_promise=False):
        params = {'expression': expression, 'returnByValue': True}
        if await_promise:
            params['awaitPromise'] = True
        eid = self.send('Runtime.evaluate', params)
        res = self.recv_result(eid, timeout)
        if res and 'result' in res and 'value' in res['result']:
            return res['result']['value']
        return None

    def get_cookies(self, url_filter='feishu.cn'):
        cid = self.send('Network.getCookies')
        res = self.recv_result(cid, 10)
        if res and 'cookies' in res:
            all_cookies = res['cookies']
            return [c for c in all_cookies if url_filter in (c.get('domain', ''))]
        return []

    def get_current_url(self):
        return self.evaluate('window.location.href')

    def get_page_text(self, max_chars=10000):
        return self.evaluate(f'document.body.innerText.substring(0, {max_chars})')

    def close(self):
        self.ws.close()
