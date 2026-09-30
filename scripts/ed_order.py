# -*- coding: utf-8 -*-
"""
ed_order.py - 订单管理 + 统计查询自动化

页面：
  订单管理：https://ed.weeeg.com/ekadmin/order/list
  统计查询：https://ed.weeeg.com/ekadmin/statistic/order

订单状态 tab：全部/待付款/待发货/待收货/退款中/交易完成/交易关闭/黑名单/待评价
订单表列：店铺/订单编号/商品信息/用户信息/实收款/数量/订单状态/支付时间/备注/操作

统计卡片：
  销售订单(笔)：今日/昨日/日环比/成交订单总量
  销售金额(元)：今日/昨日/日环比/销售总额
  退款金额(元)：今日/昨日/日环比/本月退款
  购买用户：今日/昨日/日环比/总用户数
  状态角标：待付款/待发货/待收货/退款中
  图表：营业趋势/订单来源分析/订单类型分析

用法：
    from ed_order import EDOrder
    o = EDOrder()
    o.connect()
    orders = o.list_orders(status="全部")
    stats = o.get_sales_stats()
"""

import sys
import os
import json
import time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp_tools import EDClient

ORDER_URL = "https://ed.weeeg.com/ekadmin/order/list"
STAT_URL = "https://ed.weeeg.com/ekadmin/statistic/order"

ORDER_STATUS = ["全部", "待付款", "待发货", "待收货", "退款中", "交易完成", "交易关闭", "黑名单", "待评价"]


class EDOrder(EDClient):
    """订单+统计自动化客户端"""

    # ---------- 订单管理 ----------

    def open_order_page(self):
        self.navigate(ORDER_URL, wait=6)
        self.clear_loading_masks()
        self.wait_for_rows(timeout=20)

    def switch_order_status(self, status="全部"):
        """切换订单状态 tab"""
        if status not in ORDER_STATUS:
            return f"INVALID_STATUS: {status}"
        if status == "全部":
            return "DEFAULT"
        pos = self.eval(f"""(() => {{
            const tabs = document.querySelectorAll('.el-tabs__item, [role=tab]');
            const t = [...tabs].find(t => t.textContent.trim() === '{status}' && t.offsetParent !== null);
            if(!t) return 'NOT_FOUND';
            const r = t.getBoundingClientRect();
            return JSON.stringify({{x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2)}});
        }})()""")
        try:
            c = json.loads(pos)
            self.mouse_click(c["x"], c["y"])
            self.sleep(3)
            self.clear_loading_masks()
            return "SWITCHED"
        except Exception:
            return pos

    def list_orders(self, status="全部", max_rows=50):
        """读取订单列表"""
        self.open_order_page()
        if status != "全部":
            self.switch_order_status(status)
        res = self.eval(f"""(() => {{
            const rows = document.querySelectorAll('.el-table__body-wrapper .el-table__row');
            return JSON.stringify([...rows].slice(0, {max_rows}).map((row, idx) => {{
                const cells = row.querySelectorAll('td .cell');
                const text = i => cells[i] ? cells[i].textContent.trim() : '';
                return {{
                    idx: idx,
                    shop: text(1),
                    order_id: text(2),
                    product: text(3).substring(0,60),
                    user: text(4),
                    amount: text(5),
                    qty: text(6),
                    status: text(7),
                    pay_time: text(8),
                    remark: text(9)
                }};
            }}));
        }})()""")
        try:
            return json.loads(res)
        except Exception:
            return [{"error": res[:300]}]

    def get_order_summary(self):
        """订单统计概览（各状态 tab 数量）"""
        self.open_order_page()
        summary = {}
        for st in ["待付款", "待发货", "待收货", "退款中"]:
            self.switch_order_status(st)
            cnt = self.eval("document.querySelectorAll('.el-table__body-wrapper .el-table__row').length")
            summary[st] = cnt
        # 回全部
        self.switch_order_status("全部")
        return summary

    def goto_evaluation(self):
        """去评价管理"""
        pos = self.eval("""(() => {
            const items = document.querySelectorAll('.el-menu-item, [class*=menu-item]');
            const k = [...items].find(i => i.textContent.trim() === '评价管理' && i.offsetParent !== null);
            if(!k) return 'NOT_FOUND';
            const r = k.getBoundingClientRect();
            return JSON.stringify({x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2)});
        })()""")
        try:
            c = json.loads(pos)
            self.mouse_click(c["x"], c["y"])
            self.sleep(3)
            return self.get_page_text(800)
        except Exception:
            return pos

    # ---------- 统计查询 ----------

    def open_stat_page(self, tab="订单统计"):
        """打开统计查询页（默认订单统计）"""
        self.navigate(STAT_URL, wait=6)
        self.clear_loading_masks()
        time.sleep(2)
        # 切换 订单统计/商品统计 tab
        if tab == "商品统计":
            pos = self.eval("""(() => {
                const tabs = document.querySelectorAll('.el-tabs__item, [role=tab], [class*=tab]');
                for(const t of tabs) {
                    if(t.textContent.trim() === '商品统计' && t.offsetParent !== null) {
                        const r = t.getBoundingClientRect();
                        return JSON.stringify({x: Math.round(r.left + r.width/2), y: Math.round(r.top + r.height/2)});
                    }
                }
                return 'NOT_FOUND';
            })()""")
            try:
                c = json.loads(pos)
                self.mouse_click(c["x"], c["y"])
                self.sleep(3)
                self.clear_loading_masks()
            except Exception:
                pass
        return self.eval("document.title")

    def get_sales_stats(self):
        """
        读取销售数据统计卡片
        返回 {销售订单:{today, yesterday, mom, total}, 销售金额:{...}, 退款金额:{...}, 购买用户:{...}, 待付款/待发货/待收货/退款中}
        """
        self.open_stat_page(tab="订单统计")
        # 通过 DOM 精确读取各统计卡片
        res = self.eval("""(() => {
            // 方法：读所有可见 el-card 的文本，按已知标题定位
            const body = document.body.innerText;
            return body.substring(body.indexOf('销售数据统计'), body.indexOf('销售数据统计') + 2000);
        })()""")
        return res

    def read_stat_text(self, max_len=2500):
        """读取统计页当前全部文本"""
        self.open_stat_page(tab="订单统计")
        return self.get_page_text(max_len)


if __name__ == "__main__":
    o = EDOrder()
    o.connect()

    print("=== 1. 订单列表 ===")
    orders = o.list_orders(status="全部")
    print(f"  共 {len(orders) if isinstance(orders, list) else 'N/A'} 条")
    for od in (orders if isinstance(orders, list) else []):
        if "error" in od:
            print("  ERROR:", od["error"])
            break
        print(f"  #{od['idx']} [{od['order_id']}] {od['product'][:30]} | {od['user']} | {od['amount']} | {od['status']}")

    print("\n=== 2. 待发货订单数 ===")
    cnt = o.switch_order_status("待发货")
    n = o.eval("document.querySelectorAll('.el-table__body-wrapper .el-table__row').length")
    print(f"  待发货: {n} 条")

    print("\n=== 3. 销售统计 ===")
    stats = o.get_sales_stats()
    print(stats[:1500])

    o.close()
    print("\n=== 完成 ===")
