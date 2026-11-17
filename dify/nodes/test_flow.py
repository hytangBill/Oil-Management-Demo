import json, importlib.util, sys
def load(p):
    spec=importlib.util.spec_from_file_location(p,p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
A=load('node_a_state_menu.py'); R=load('node_1_recipe.py'); M=load('node_2_model.py'); P=load('node_3_policy.py'); C=load('node_4_compose.py')
state="{}"
def turn(q, llm=None, show=False):
    global state
    a=A.main(q,state)
    if a['route']!='submit':
        state=a['new_state']
        if show: print(a['reply_md'])
        return a['reply_md']
    r=R.main(a['new_state']); m=M.main(a['new_state'], r['order_json']); p=P.main(m['model_json'])
    if llm is None:
        d=json.loads(p['decision_json'])['decisions']
        llm=json.dumps({v:{"action":d[v]['recommended'],"reason":"Test reason without digits."} for v in d}|{"shift_summary":"All good."})
    c=C.main(llm, a['new_state'], m['model_json'], p['decision_json'], r['order_md'], r['order_json'])
    state=c['final_state']
    if show: print(p['llm_facts']); print(c['final_md'])
    print('model_json chars', len(m['model_json']))
    return c['final_md']
turn("hello")
turn("TIME:12:00")
for sku in ['fries_l','fries_l','nuggets_9','big_mac']: turn('ADD:'+sku)
print(turn('SUBMIT')[:300])
turn('ADD:mccrispy')
turn('SUBMIT', show=True)
