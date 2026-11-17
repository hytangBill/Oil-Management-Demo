import json
exec(open('test_flow.py').read().split('turn("hello")')[0])
turn("TIME:18:00")
for i in range(26):
    for sku in ['fries_l']*3+['nuggets_20','mckroket']: turn('ADD:'+sku)
    md=turn('SUBMIT')
    s=json.loads(state); 
    hdr=[l for l in md.splitlines() if l.startswith('### ')]
    print(A.fmt_clock(s['clock']), round(s['vats']['F1']['tpm'],2), round(s['vats']['C1']['tpm'],2), '|', ' / '.join(hdr))
# operator action + bad llm
print(turn('ACT:C1:CHANGE')[:400])
for sku in ['fries_m']*5: turn('ADD:'+sku)
md=turn('SUBMIT', llm='{"F1":{"reason":"Oil is at 23%"},"C1":{"reason":"fine"}}')
print([l for l in md.splitlines() if 'Why' in l or 'fallback' in l])
print(turn('blah blah')[:500])
