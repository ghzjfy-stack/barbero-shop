/**
 * Telegram control menu for BARBERO orders (inline keyboards + parsers).
 */
import { escapeHtml, formatIls, formatWhen } from "./telegramOrderCard.js";

export const STATUS_BY_KEY = {
  paid: "שולם",
  cancel: "בוטל",
  prep: "בהכנה",
  ship: "משלוח מארה״ב",
  done: "נמסר",
};

export const FILTER_LABELS = {
  wait: "ממתינים לתשלום",
  paid: "שולם",
  prep: "בהכנה",
  ship: "במשלוח",
  done: "נמסר",
  cancel: "בוטל",
  all: "הכל (אחרונות)",
};

export function buildMainMenuKeyboard(counts = {}) {
  const c = (key) => (counts[key] != null ? ` (${counts[key]})` : "");
  return {
    inline_keyboard: [
      [
        { text: `⏳ ממתינים${c("wait")}`, callback_data: "brb:list:wait" },
        { text: `✅ שולם${c("paid")}`, callback_data: "brb:list:paid" },
      ],
      [
        { text: `🛠 בהכנה${c("prep")}`, callback_data: "brb:list:prep" },
        { text: `✈️ משלוח${c("ship")}`, callback_data: "brb:list:ship" },
      ],
      [
        { text: `📦 נמסר${c("done")}`, callback_data: "brb:list:done" },
        { text: `❌ בוטל${c("cancel")}`, callback_data: "brb:list:cancel" },
      ],
      [{ text: `🗂 כל ההזמנות האחרונות${c("all")}`, callback_data: "brb:list:all" }],
      [
        { text: "🩺 בדיקת סנכרון", callback_data: "brb:health" },
        { text: "🔄 רענון תפריט", callback_data: "brb:menu" },
      ],
    ],
  };
}

export function buildMainMenuText(counts = {}) {
  const line = (label, key) =>
    counts[key] != null ? `• ${label}: <b>${counts[key]}</b>` : `• ${label}`;
  return [
    "📋 <b>BARBERO — ניהול הזמנות</b>",
    "",
    "בחרו רשימה או בדקו סנכרון:",
    line("ממתינים לתשלום", "wait"),
    line("שולם", "paid"),
    line("בהכנה", "prep"),
    line("במשלוח", "ship"),
    line("נמסר", "done"),
    line("בוטל", "cancel"),
    line("סה״כ", "all"),
    "",
    "טיפ: אפשר גם לשלוח מספר הזמנה (BRB-… ) בצ׳אט.",
  ].join("\n");
}

export function buildOrdersListText(filter, orders = []) {
  const label = FILTER_LABELS[filter] || filter;
  if (!orders.length) {
    return `📭 <b>${escapeHtml(label)}</b>\n\nאין הזמנות בקטגוריה הזו כרגע.`;
  }
  const lines = orders.map((order, index) => {
    const number = order.number || order.orderNumber || "—";
    const name = order.details?.name || order.name || "—";
    const total = formatIls(order.total);
    const status = order.status || "—";
    const when = formatWhen(order.createdAt);
    return `${index + 1}. <b>#${escapeHtml(number)}</b> · ${escapeHtml(status)}\n   ${escapeHtml(name)} · ${escapeHtml(total)} · ${escapeHtml(when)}`;
  });
  return [`📋 <b>${escapeHtml(label)}</b> — ${orders.length}`, "", ...lines, "", "לחצו על הזמנה לפתיחת כרטיס ניהול:"].join(
    "\n",
  );
}

export function buildOrdersListKeyboard(filter, orders = []) {
  const rows = (orders || []).slice(0, 10).map((order) => {
    const number = String(order.number || order.orderNumber || "").trim().slice(0, 24);
    const name = String(order.details?.name || order.name || "").trim().slice(0, 18);
    return [
      {
        text: `#${number}${name ? ` · ${name}` : ""}`,
        callback_data: `brb:open:${number}`,
      },
    ];
  });
  rows.push([
    { text: "◀️ תפריט ראשי", callback_data: "brb:menu" },
    { text: "🔄 רענון", callback_data: `brb:list:${filter || "all"}` },
  ]);
  return { inline_keyboard: rows };
}

export function buildReplyMenuKeyboard() {
  return {
    keyboard: [
      [{ text: "📋 תפריט הזמנות" }, { text: "⏳ ממתינים" }],
      [{ text: "✅ שולם" }, { text: "✈️ משלוח" }],
      [{ text: "🩺 סנכרון" }, { text: "🗂 אחרונות" }],
    ],
    resize_keyboard: true,
    is_persistent: true,
  };
}

/** Parse callback_data for menu + order actions (legacy a/c/r still work). */
export function parseMenuCallback(data) {
  const raw = String(data || "").trim();
  if (!raw.startsWith("brb:")) return null;

  if (raw === "brb:menu" || raw === "brb:m") return { kind: "menu", action: "home" };
  if (raw === "brb:health") return { kind: "menu", action: "health" };

  let match = /^brb:list:([a-z]+)$/.exec(raw);
  if (match) return { kind: "menu", action: "list", filter: match[1] };

  match = /^brb:open:(.+)$/.exec(raw);
  if (match) return { kind: "order", action: "open", orderNumber: match[1].trim() };

  match = /^brb:set:([a-z]+):(.+)$/.exec(raw);
  if (match) {
    const statusKey = match[1];
    const status = STATUS_BY_KEY[statusKey];
    if (!status) return null;
    return {
      kind: "order",
      action: "setStatus",
      statusKey,
      status,
      orderNumber: match[2].trim(),
    };
  }

  // Legacy Minox-style: brb:a|c|r:ORDER
  match = /^brb:([acr]):(.+)$/.exec(raw);
  if (match) {
    const action = { a: "approve", c: "cancel", r: "refresh" }[match[1]];
    if (!action) return null;
    if (action === "approve") {
      return {
        kind: "order",
        action: "setStatus",
        statusKey: "paid",
        status: "שולם",
        orderNumber: match[2].trim(),
      };
    }
    if (action === "cancel") {
      return {
        kind: "order",
        action: "setStatus",
        statusKey: "cancel",
        status: "בוטל",
        orderNumber: match[2].trim(),
      };
    }
    return { kind: "order", action: "refresh", orderNumber: match[2].trim() };
  }

  return null;
}

export function parseTextCommand(text) {
  const raw = String(text || "").trim();
  if (!raw) return null;
  const lower = raw.toLowerCase();

  if (
    lower === "/start" ||
    lower === "/menu" ||
    raw === "📋 תפריט הזמנות" ||
    raw === "תפריט" ||
    raw === "menu"
  ) {
    return { action: "home" };
  }
  if (lower === "/health" || lower === "/sync" || raw === "🩺 סנכרון" || raw === "סנכרון") {
    return { action: "health" };
  }
  if (lower === "/orders" || raw === "🗂 אחרונות" || raw === "אחרונות") {
    return { action: "list", filter: "all" };
  }
  if (raw === "⏳ ממתינים" || lower === "/wait") return { action: "list", filter: "wait" };
  if (raw === "✅ שולם" || lower === "/paid") return { action: "list", filter: "paid" };
  if (raw === "✈️ משלוח" || lower === "/ship") return { action: "list", filter: "ship" };

  const orderMatch = raw.match(/\b(BRB-?[A-Z0-9-]+)\b/i);
  if (orderMatch) {
    return { action: "open", orderNumber: orderMatch[1].toUpperCase().replace(/^BRB(?!-)/, "BRB-") };
  }
  return null;
}
