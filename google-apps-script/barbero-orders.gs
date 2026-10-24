/**
 * BARBERO → Google Sheets (הזמנות אוטומטיות + עיצוב)
 *
 * התקנה / עדכון (חובה אחרי שינוי קוד — אחרת מיילים נופלים לטאב הזמנות):
 * 1. Extensions → Apps Script → מחקו הכול והדביקו את הקובץ הזה
 * 2. שמרו
 * 3. בחרו setupBarberoSheet → Run (פעם אחת) — יוצר גם טאב «ניוזלטר»
 * 4. Deploy → Manage deployments → עיפרון → New version → Deploy
 *
 * בלי עמודות שותפים. הזמנות → טאב «הזמנות». מיילים → טאב «ניוזלטר».
 */

var SPREADSHEET_ID = "1024eC15y0slevJ-aESRrLzshAnOCoArxV6jcZnouJeQ";
var SHEET_NAME = "הזמנות";
var NEWSLETTER_SHEET_NAME = "ניוזלטר";
var WEBHOOK_SECRET = "";

var NEWSLETTER_HEADERS = ["תאריך", "אימייל"];

/** כותרות — סדר חשוב ל-append מהאתר */
var HEADERS = [
  "סטטוס",
  "תאריך",
  "מספר הזמנה",
  "שם",
  "טלפון",
  "עיר",
  "כתובת",
  "דירה/קומה",
  "מיקוד",
  "הערות",
  "מוצרים",
  "סיכום ביניים",
  "משלוח",
  "סה״כ",
  "תשלום",
  "ימי משלוח",
];

var STATUS_OPTIONS = [
  "ממתין לביט",
  "ממתין ל-PayPal",
  "שולם",
  "בהכנה",
  "משלוח מארה״ב",
  "נמסר",
  "בוטל",
];

/** צבעי מותג BARBERO */
var COLOR = {
  headerBg: "#1B4332",
  headerFg: "#FFFFFF",
  stripe: "#F4F7F5",
  ink: "#0B1210",
  muted: "#5C6B64",
  gold: "#C6A15B",
  waitBit: "#FFF3CD",
  waitPaypal: "#D6EAF8",
  paid: "#D4EDDA",
  prep: "#CCE5FF",
  ship: "#1B4332",
  shipFg: "#FFFFFF",
  delivered: "#7B2D26",
  deliveredFg: "#FFFFFF",
  cancelled: "#E9ECEF",
  emptyStatus: "#F1F3F4",
};

/**
 * הרצה חד־פעמית מעורך Apps Script:
 * מעצבת את הגיליון, מוסיפה רשימות נפתחות וצבעים.
 */
function setupBarberoSheet() {
  var sheet = getSheet_();
  ensureHeader_(sheet, true);
  styleSheet_(sheet);
  applyStatusValidation_(sheet);
  applyConditionalFormat_(sheet);
  formatMoneyColumns_(sheet);
  setupNewsletterSheet_();
  SpreadsheetApp.flush();
}

function doPost(e) {
  try {
    var body = JSON.parse((e && e.postData && e.postData.contents) || "{}");
    if (WEBHOOK_SECRET && body.secret !== WEBHOOK_SECRET) {
      return json_({ ok: false, error: "unauthorized" });
    }

    // הרשמת ניוזלטר — לא לכתוב לטאב הזמנות
    if (isNewsletterPayload_(body)) {
      return appendNewsletter_(body);
    }

    var row = body.row || {};
    var orderNumber = row.orderNumber || (body.order && body.order.number) || "";
    // חוסם שורות ריקות מסוג "ממתין לביט" בלי מספר הזמנה
    if (!orderNumber) {
      return json_({ ok: false, error: "missing_order_number" });
    }

    var sheet = getSheet_();
    ensureHeader_(sheet, false);

    var payment = row.payment || "ביט";
    var status =
      row.status ||
      (payment === "PayPal" ? "ממתין ל-PayPal" : "ממתין לביט");

    sheet.appendRow([
      status,
      row.createdAt || "",
      orderNumber,
      row.name || "",
      row.phone || "",
      row.city || "",
      row.address || "",
      row.unit || "",
      row.postal || "",
      row.notes || "",
      row.items || "",
      blankToNumber_(row.subtotal),
      blankToNumber_(row.shipping),
      blankToNumber_(row.total),
      payment,
      "", // ימי משלוח — ממלאים ידנית כשהחבילה בדרך
    ]);

    var last = sheet.getLastRow();
    styleDataRow_(sheet, last);
    applyStatusValidation_(sheet);
    return json_({ ok: true, row: last });
  } catch (err) {
    return json_({ ok: false, error: String(err && err.message ? err.message : err) });
  }
}

function isNewsletterPayload_(body) {
  if (!body || typeof body !== "object") return false;
  if (body.type === "newsletter") return true;
  var email = String(body.email || "").trim();
  if (!email) return false;
  var hasOrder =
    (body.row && body.row.orderNumber) || (body.order && body.order.number);
  return !hasOrder;
}

function doGet() {
  return json_({
    ok: true,
    service: "barbero-orders",
    sheet: SHEET_NAME,
    newsletter: NEWSLETTER_SHEET_NAME,
  });
}

function appendNewsletter_(body) {
  var email = String(body.email || "")
    .trim()
    .toLowerCase();
  if (!email) return json_({ ok: false, error: "missing_email" });

  var sheet = getNewsletterSheet_();
  ensureNewsletterHeader_(sheet);

  // אל תכפיל מייל שכבר רשום
  var last = sheet.getLastRow();
  if (last >= 2) {
    var existing = sheet.getRange(2, 2, last, 2).getValues();
    for (var i = 0; i < existing.length; i++) {
      if (
        String(existing[i][0] || "")
          .trim()
          .toLowerCase() === email
      ) {
        return json_({ ok: true, duplicate: true, row: i + 2 });
      }
    }
  }

  var when = body.createdAt || formatNow_();
  sheet.appendRow([when, email]);
  var row = sheet.getLastRow();
  sheet.getRange(row, 1, 1, 2).setHorizontalAlignment("center").setVerticalAlignment("middle");
  return json_({ ok: true, row: row });
}

function getSheet_() {
  var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  var sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) sheet = ss.insertSheet(SHEET_NAME);
  sheet.setRightToLeft(true);
  return sheet;
}

function getNewsletterSheet_() {
  var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  var sheet = ss.getSheetByName(NEWSLETTER_SHEET_NAME);
  if (!sheet) sheet = ss.insertSheet(NEWSLETTER_SHEET_NAME);
  sheet.setRightToLeft(true);
  return sheet;
}

function setupNewsletterSheet_() {
  var sheet = getNewsletterSheet_();
  ensureNewsletterHeader_(sheet);
  var header = sheet.getRange(1, 1, 1, NEWSLETTER_HEADERS.length);
  header.setBackground(COLOR.headerBg);
  header.setFontColor(COLOR.headerFg);
  header.setFontWeight("bold");
  header.setFontFamily("Arial");
  header.setHorizontalAlignment("center");
  sheet.setColumnWidth(1, 140);
  sheet.setColumnWidth(2, 260);
  sheet.setFrozenRows(1);
}

function ensureNewsletterHeader_(sheet) {
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(NEWSLETTER_HEADERS);
  } else {
    sheet.getRange(1, 1, 1, NEWSLETTER_HEADERS.length).setValues([NEWSLETTER_HEADERS]);
  }
}

function formatNow_() {
  return Utilities.formatDate(new Date(), "Asia/Jerusalem", "dd.MM.yyyy, HH:mm");
}

function ensureHeader_(sheet, forceRestyle) {
  var lastRow = sheet.getLastRow();
  if (lastRow === 0) {
    sheet.appendRow(HEADERS);
  } else {
    // אם חסרה עמודת ימי משלוח — מוסיפים בסוף בלי לשבור נתונים קיימים
    var width = sheet.getLastColumn();
    var headers = sheet.getRange(1, 1, 1, Math.max(width, HEADERS.length)).getValues()[0];
    var hasShipDays = false;
    for (var i = 0; i < headers.length; i++) {
      if (String(headers[i]).indexOf("ימי משלוח") !== -1) {
        hasShipDays = true;
        break;
      }
    }
    if (!hasShipDays) {
      sheet.getRange(1, HEADERS.length).setValue("ימי משלוח");
    } else {
      sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
    }
  }

  if (forceRestyle || lastRow === 0) {
    styleSheet_(sheet);
  } else {
    styleHeaderOnly_(sheet);
  }
  sheet.setFrozenRows(1);
}

function styleSheet_(sheet) {
  styleHeaderOnly_(sheet);

  var maxRows = Math.max(sheet.getMaxRows(), 200);
  var cols = HEADERS.length;

  // רוחב עמודות נוח למובייל / דסקטופ
  var widths = [140, 130, 120, 120, 110, 90, 160, 90, 80, 140, 220, 100, 80, 90, 90, 90];
  for (var c = 0; c < widths.length; c++) {
    sheet.setColumnWidth(c + 1, widths[c]);
  }

  // שורות נתונים — יישור וגופן
  if (sheet.getLastRow() > 1) {
    var data = sheet.getRange(2, 1, sheet.getLastRow() - 1, cols);
    data.setFontFamily("Arial");
    data.setFontSize(10);
    data.setVerticalAlignment("middle");
    data.setHorizontalAlignment("center");
    data.setWrap(true);
  }

  // רקע עדין לשורות ריקות בסטטוס
  sheet.getRange(2, 1, maxRows - 1, 1).setBackground(COLOR.emptyStatus);

  formatMoneyColumns_(sheet);
  applyStatusValidation_(sheet);
  applyConditionalFormat_(sheet);
}

function styleHeaderOnly_(sheet) {
  var header = sheet.getRange(1, 1, 1, HEADERS.length);
  header.setValues([HEADERS]);
  header.setBackground(COLOR.headerBg);
  header.setFontColor(COLOR.headerFg);
  header.setFontWeight("bold");
  header.setFontFamily("Arial");
  header.setFontSize(11);
  header.setHorizontalAlignment("center");
  header.setVerticalAlignment("middle");
  sheet.setRowHeight(1, 36);
}

function styleDataRow_(sheet, row) {
  var range = sheet.getRange(row, 1, 1, HEADERS.length);
  range.setFontFamily("Arial");
  range.setFontSize(10);
  range.setVerticalAlignment("middle");
  range.setHorizontalAlignment("center");
  range.setWrap(true);
  if (row % 2 === 0) {
    // לא דורסים צבע סטטוס — רק עמודות אחרות ברקע עדין
    sheet.getRange(row, 2, 1, HEADERS.length - 1).setBackground(COLOR.stripe);
  }
  sheet.getRange(row, 12, 1, 3).setNumberFormat("₪#,##0");
  sheet.getRange(row, 16).setNumberFormat("0");
}

function formatMoneyColumns_(sheet) {
  var last = sheet.getLastRow();
  if (last < 2) return;
  sheet.getRange(2, 12, last - 1, 3).setNumberFormat("₪#,##0");
  sheet.getRange(2, 16, last - 1, 1).setNumberFormat("0");
}

function applyStatusValidation_(sheet) {
  var maxRows = Math.max(sheet.getMaxRows(), 200);
  var rule = SpreadsheetApp.newDataValidation()
    .requireValueInList(STATUS_OPTIONS, true)
    .setAllowInvalid(false)
    .setHelpText("בחרו סטטוס הזמנה")
    .build();
  sheet.getRange(2, 1, maxRows - 1, 1).setDataValidation(rule);
}

function applyConditionalFormat_(sheet) {
  sheet.clearConditionalFormatRules();
  var maxRows = Math.max(sheet.getMaxRows(), 500);
  var statusRange = sheet.getRange(2, 1, maxRows - 1, 1);
  var daysRange = sheet.getRange(2, 16, maxRows - 1, 1);
  var rules = [];

  function statusRule(text, bg, fg) {
    return SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo(text)
      .setBackground(bg)
      .setFontColor(fg || COLOR.ink)
      .setRanges([statusRange])
      .build();
  }

  rules.push(statusRule("ממתין לביט", COLOR.waitBit));
  rules.push(statusRule("ממתין ל-PayPal", COLOR.waitPaypal));
  rules.push(statusRule("שולם", COLOR.paid));
  rules.push(statusRule("בהכנה", COLOR.prep));
  rules.push(statusRule("משלוח מארה״ב", COLOR.ship, COLOR.shipFg));
  rules.push(statusRule("נמסר", COLOR.delivered, COLOR.deliveredFg));
  rules.push(statusRule("בוטל", COLOR.cancelled, COLOR.muted));

  // סולם צבעים לימי משלוח (כמו במינוקס) — ירוק קצר → אדום ארוך
  rules.push(
    SpreadsheetApp.newConditionalFormatRule()
      .setGradientMinpointWithValue("#D8F3DC", SpreadsheetApp.InterpolationType.NUMBER, "5")
      .setGradientMidpointWithValue("#FFE066", SpreadsheetApp.InterpolationType.NUMBER, "12")
      .setGradientMaxpointWithValue("#F8AD9D", SpreadsheetApp.InterpolationType.NUMBER, "20")
      .setRanges([daysRange])
      .build(),
  );

  sheet.setConditionalFormatRules(rules);
}

function blankToNumber_(value) {
  if (value === "" || value == null) return "";
  var n = Number(value);
  return isNaN(n) ? "" : n;
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(
    ContentService.MimeType.JSON,
  );
}
