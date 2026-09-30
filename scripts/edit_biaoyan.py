# -*- coding: utf-8 -*-
"""原地编辑 6 个无人机表演宝贝：改标题/描述/价格并保存"""
import sys, io, json, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from ed_product import EDProduct

IDS = ["1077854738546","1074550698790","1073613999098","1073988642744","1028157586875","1070773126255"]

NEW_TITLE = "【宜昌】固定翼飞行表演 开业庆典 1000元/架 带飞手"
NEW_PRICE = "1000"
NEW_DESC = """【宜昌】固定翼飞行表演 开业庆典 活动暖场
【价格】1000元/架（带全套设备、带专业飞手）
【飞行时长】单次飞行3~5分钟
【服务内容】
1、固定翼飞行表演：开业/庆典/活动暖场造势，视觉震撼吸睛
2、设备飞手全包：全套飞行设备+专业飞手到场即飞，您什么都不用准备
3、可按活动需求定制飞行方案
【预约须知】
需提前沟通飞行地点，我们协助确认是否禁飞区、是否需要报备，合规飞行更放心
【服务方式】宜昌及周边，建议提前预约档期
【另接】无人机编队灯光秀（图案/文字/LOGO定制），详询
【承诺】专业团队执行，安全第一"""

p = EDProduct()
p.connect()

for pid in IDS:
    p.eval(f"location.href = 'https://ed.weeeg.com/ekadmin/product/add_product/{pid}'")
    p.sleep(4)
    payload = json.dumps({"t": NEW_TITLE, "d": NEW_DESC, "pr": NEW_PRICE})
    r = p.eval(f"""(() => {{
        const data = {payload};
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        const tsetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
        let done = {{title:false, desc:false, price:false}};
        document.querySelectorAll('input').forEach(i => {{
            const label = i.closest('.el-form-item')?.querySelector('label')?.textContent?.trim() || '';
            if(label.includes('宝贝标题')) {{ setter.call(i, data.t); i.dispatchEvent(new Event('input',{{bubbles:true}})); done.title = true; }}
            if(label.includes('售价')) {{ setter.call(i, data.pr); i.dispatchEvent(new Event('input',{{bubbles:true}})); done.price = true; }}
        }});
        document.querySelectorAll('textarea').forEach(t => {{
            const label = t.closest('.el-form-item')?.querySelector('label')?.textContent?.trim() || '';
            if(label.includes('宝贝描述')) {{ tsetter.call(t, data.d); t.dispatchEvent(new Event('input',{{bubbles:true}})); done.desc = true; }}
        }});
        return JSON.stringify(done);
    }})()""")
    print(pid, "填写:", r)
    if '"title":true' not in r or '"desc":true' not in r:
        print(pid, "!! 字段没填全，跳过保存")
        continue
    # 点保存
    s = p.eval("""(() => {
        const btns = [...document.querySelectorAll('button')];
        const b = btns.find(x => x.textContent.trim() === '保存' && x.offsetParent !== null);
        if(!b) return 'NO_SAVE_BTN';
        b.click();
        return 'CLICKED_SAVE';
    })()""")
    print(pid, "保存:", s)
    p.sleep(3)
    # 读提示
    msg = p.eval("""(() => {
        const m = document.querySelector('.el-message, .el-message-box');
        return m ? m.textContent.trim().slice(0,60) : 'NO_MSG';
    })()""")
    print(pid, "提示:", msg)

p.close()
print("ALL_DONE")
