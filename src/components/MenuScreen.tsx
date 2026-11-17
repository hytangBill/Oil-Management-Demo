import { Clock, Info, Minus, Plus, ShoppingBag, Trash2, X } from 'lucide-react';
import { useState } from 'react';
import type { DifyStateResponse } from '../types/dify';
import { OperatorActionsBar } from './OperatorActionsBar';

interface MenuScreenProps {
  data: DifyStateResponse;
  isLoading: boolean;
  onCommand: (cmd: string) => void;
}

export function MenuScreen({ data, isLoading, onCommand }: MenuScreenProps) {
  const [showTimePicker, setShowTimePicker] = useState(false);

  const cartQtyMap = new Map<string, number>();
  for (const item of data.cart || []) {
    cartQtyMap.set(item.sku, item.qty);
  }

  const cartCount = data.cart_count ?? 0;
  const minItems = data.min_items ?? 0;
  const remaining = minItems > cartCount ? minItems - cartCount : 0;
  const progressPct = minItems > 0 ? Math.min(100, (cartCount / minItems) * 100) : 100;

  return (
    <div className="max-w-[1440px] mx-auto px-4 sm:px-6 py-5 space-y-6">
      {/* Top Info Bar + Change Time Slot Toggle */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        {data.note ? (
          <div className="flex-1 min-w-[260px] bg-white border border-[#E5DDD0] rounded-2xl px-4 py-3 flex items-center gap-2.5 text-sm text-[#27251F]">
            <Info className="w-4 h-4 text-[#D62300] shrink-0" />
            <span>{data.note}</span>
          </div>
        ) : (
          <div />
        )}

        {data.time_slots && data.time_slots.length > 0 && (
          <button
            type="button"
            disabled={isLoading}
            onClick={() => setShowTimePicker((prev) => !prev)}
            className="min-h-[56px] px-4 py-2.5 rounded-2xl bg-[#FFC72C] hover:bg-[#F2B705] text-[#27251F] font-semibold text-sm flex items-center gap-2 transition-colors cursor-pointer whitespace-nowrap shrink-0 disabled:opacity-50"
          >
            <Clock className="w-4 h-4" />
            <span>Change time slot</span>
          </button>
        )}
      </div>

      {/* Client-side Time Slots Picker Drawer */}
      {showTimePicker && data.time_slots && data.time_slots.length > 0 && (
        <section className="bg-white border-2 border-[#FFC72C] rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between gap-3">
            <h2 className="font-display font-bold text-lg text-[#27251F]">
              Select Time Slot
            </h2>
            <button
              type="button"
              onClick={() => setShowTimePicker(false)}
              className="min-h-[56px] min-w-[56px] rounded-2xl bg-[#FFF8E7] hover:bg-[#F3EDE3] flex items-center justify-center text-[#27251F] cursor-pointer"
              aria-label="Close time slot picker"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {data.time_slots.map((slot) => {
              const isSelected = data.clock === slot.time;
              return (
                <button
                  key={slot.time}
                  type="button"
                  disabled={isLoading}
                  onClick={() => {
                    setShowTimePicker(false);
                    onCommand(`TIME:${slot.time}`);
                  }}
                  className={`min-h-[72px] p-4 rounded-2xl border-2 text-left transition-all cursor-pointer active:scale-[0.98] flex flex-col justify-center gap-1 disabled:opacity-50 ${
                    isSelected
                      ? 'bg-[#FFC72C]/25 border-[#FFC72C]'
                      : 'bg-[#FFF8E7] border-[#E5DDD0] hover:border-[#FFC72C]'
                  }`}
                >
                  <span className="font-display font-bold text-base text-[#D62300] tabular-nums">
                    {slot.time}
                  </span>
                  <span className="font-semibold text-sm text-[#27251F]">{slot.label}</span>
                </button>
              );
            })}
          </div>
        </section>
      )}

      {/* Main 2-Column Tablet POS Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left: Menu Sections ONLY from data.menu */}
        <div className="lg:col-span-8 space-y-6">
          {(data.menu || []).map((section) => (
            <section key={section.section} className="space-y-3">
              <h2 className="font-display font-bold text-xl text-[#27251F]">
                {section.section}
              </h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {(section.items || []).map((item) => {
                  const qty = cartQtyMap.get(item.sku) ?? 0;

                  return (
                    <div
                      key={item.sku}
                      className={`relative rounded-2xl border p-4 flex items-center justify-between gap-3 min-h-[80px] transition-colors ${
                        qty > 0
                          ? 'bg-white border-[#FFC72C] ring-2 ring-[#FFC72C]/40'
                          : 'bg-white border-[#E5DDD0]'
                      }`}
                    >
                      <div className="flex items-center gap-3 min-w-0 flex-1">
                        <span className="font-display font-semibold text-base text-[#27251F] leading-snug">
                          {item.name}
                        </span>
                        {qty > 0 && (
                          <span className="inline-flex items-center justify-center min-w-[28px] h-7 px-2 rounded-full bg-[#FFC72C] text-[#27251F] font-bold text-sm tabular-nums shrink-0">
                            {qty}
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        {qty > 0 && (
                          <button
                            type="button"
                            disabled={isLoading}
                            onClick={() => onCommand(`DEL:${item.sku}`)}
                            aria-label={`Remove ${item.name}`}
                            className="min-w-[56px] min-h-[56px] rounded-2xl bg-[#FFF8E7] hover:bg-[#E7E2D8] border border-[#D8CFC0] text-[#27251F] flex items-center justify-center cursor-pointer active:scale-95 disabled:opacity-50"
                          >
                            <Minus className="w-5 h-5" />
                          </button>
                        )}
                        <button
                          type="button"
                          disabled={isLoading}
                          onClick={() => onCommand(`ADD:${item.sku}`)}
                          aria-label={`Add ${item.name}`}
                          className="min-w-[56px] min-h-[56px] rounded-2xl bg-[#FFC72C] hover:bg-[#F2B705] text-[#27251F] flex items-center justify-center cursor-pointer active:scale-95 disabled:opacity-50"
                        >
                          <Plus className="w-5 h-5" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </section>
          ))}
        </div>

        {/* Right Panel: Order */}
        <aside className="lg:col-span-4 lg:sticky lg:top-[110px] bg-white border border-[#E5DDD0] rounded-2xl p-5 flex flex-col gap-4">
          <div className="flex items-center justify-between gap-3 pb-3 border-b border-[#E5DDD0]">
            <div className="flex items-center gap-2.5">
              <ShoppingBag className="w-5 h-5 text-[#D62300]" />
              <h2 className="font-display font-bold text-xl text-[#27251F]">Order</h2>
            </div>

            <button
              type="button"
              disabled={isLoading || cartCount === 0}
              onClick={() => onCommand('CLEAR')}
              className="min-h-[56px] px-4 rounded-2xl bg-[#FFF8E7] hover:bg-[#FDECEF] text-[#C8102E] font-semibold text-sm flex items-center gap-1.5 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <Trash2 className="w-4 h-4" />
              <span>Clear</span>
            </button>
          </div>

          {/* Progress Bar: cart_count / min_items */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs font-semibold text-[#6B6459]">
              <span className="tabular-nums">
                {cartCount} / {minItems} items
              </span>
              {!data.can_submit && (
                <span className="text-[#D62300]">
                  Add {remaining} more {remaining === 1 ? 'item' : 'items'}
                </span>
              )}
            </div>
            <div className="h-2.5 w-full rounded-full bg-[#F3EDE3] overflow-hidden">
              <div
                className={`h-full transition-all duration-200 ${
                  data.can_submit ? 'bg-[#2E9E5B]' : 'bg-[#FFC72C]'
                }`}
                style={{ width: `${progressPct}%` }}
              />
            </div>
          </div>

          {/* Cart Items */}
          <div className="max-h-[340px] overflow-y-auto divide-y divide-[#F3EDE3]">
            {(data.cart || []).length === 0 ? (
              <div className="py-8 text-center text-sm text-[#6B6459]">
                Tap + on menu items to add to the order.
              </div>
            ) : (
              data.cart.map((line) => (
                <div key={line.sku} className="py-3 flex items-center justify-between gap-2">
                  <span className="font-semibold text-sm text-[#27251F] flex-1 min-w-0">
                    {line.name}
                  </span>
                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      type="button"
                      disabled={isLoading}
                      onClick={() => onCommand(`DEL:${line.sku}`)}
                      aria-label={`Remove ${line.name}`}
                      className="min-w-[56px] min-h-[56px] rounded-2xl bg-[#FFF8E7] hover:bg-[#E7E2D8] border border-[#D8CFC0] flex items-center justify-center cursor-pointer disabled:opacity-50"
                    >
                      <Minus className="w-4 h-4" />
                    </button>
                    <span className="w-8 text-center font-bold text-base tabular-nums text-[#27251F]">
                      {line.qty}
                    </span>
                    <button
                      type="button"
                      disabled={isLoading}
                      onClick={() => onCommand(`ADD:${line.sku}`)}
                      aria-label={`Add ${line.name}`}
                      className="min-w-[56px] min-h-[56px] rounded-2xl bg-[#FFC72C] hover:bg-[#F2B705] flex items-center justify-center cursor-pointer disabled:opacity-50"
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Submit Order Button */}
          <button
            type="button"
            disabled={isLoading || !data.can_submit}
            onClick={() => onCommand('SUBMIT')}
            className="w-full min-h-[60px] px-5 py-3 rounded-2xl bg-[#D62300] hover:bg-[#B81D00] disabled:bg-[#E7E2D8] disabled:text-[#8E867A] text-white font-display font-bold text-lg transition-colors cursor-pointer disabled:cursor-not-allowed active:scale-[0.98]"
          >
            Submit order
          </button>
        </aside>
      </div>

      {/* Bottom Strip: Operator Actions */}
      <OperatorActionsBar vats={data.vats} isLoading={isLoading} onCommand={onCommand} />
    </div>
  );
}
