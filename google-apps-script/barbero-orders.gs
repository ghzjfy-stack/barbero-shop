/**
 * BARBERO → Google Sheets (סגנון מינוקס: הזמנות + רווחים + סיכומים)
 *
 * התקנה / עדכון (חובה אחרי שינוי קוד):
 * 1. Extensions → Apps Script → מחקו הכול והדביקו את הקובץ הזה
 * 2. שמרו
 * 3. בחרו setupBarberoSheet → Run (פעם אחת)
 *    — בונה טאבים: הזמנות / סיכומים / קידום ממומן / ניוזלטר
 *    — מוסיף נוסחאות רווח (מחיר − עלות מוצר − עלות משלוח)
 * 4. Deploy → Manage deployments → עיפרון → New version → Deploy
 *
 * איפוס דמו: resetBarberoDemoData → Run
 *
 * מעקב מהאתר: POST { type:"track", orderNumber? , phone? }
 * איפוס מרחוק: POST { type:"reset", confirm:"BARBERO_RESET_DEMO" }
 *
 * עמודות הזמנות (כמו מינוקס):
 *  A סטטוס | B ימי משלוח | C מספר הזמנה | D תאריך | E שם
 *  F שולם | G תשלום | H מחיר סופי | I עלות מוצר | J עלות משלוח
 *  K רווח (=H−I−J) | L לשותף (=K/2) | M חלוקה | N מוצרים
 *  O כל הנתונים | P מספר מעקב | Q סטטוס משלוח | R טלפון | S אימייל
 */

var SPREADSHEET_ID = "1024eC15y0slevJ-aESRrLzshAnOCoArxV6jcZnouJeQ";
var SHEET_NAME = "הזמנות";
var SUMMARY_SHEET_NAME = "סיכומים";
var ADS_SHEET_NAME = "קידום ממומן";
var NEWSLETTER_SHEET_NAME = "ניוזלטר";
var WEBHOOK_SECRET = "";

var NEWSLETTER_HEADERS = ["תאריך", "אימייל"];

var ADS_HEADERS = ["תאריך", "פלטפורמה", "סכום ₪", "הערות"];

/** כותרות — סדר חשוב ל-append מהאתר */
var HEADERS = [
  "סטטוס", // A
  "ימי משלוח", // B
  "מספר הזמנה", // C
  "תאריך", // D
  "שם", // E
  "שולם", // F
  "תשלום", // G
  "מחיר סופי", // H
  "עלות מוצר", // I  — ממלאים ידנית
  "עלות משלוח", // J  — ממלאים ידנית (עלות אמיתית מארה״ב)
  "רווח", // K  — נוסחה
  "לשותף", // L  — נוסחה (חצי רווח)
  "חלוקה", // M
  "מוצרים", // N
  "כל הנתונים", // O
  "מספר מעקב", // P
  "סטטוס משלוח", // Q
  "טלפון", // R — למעקב באתר
  "אימייל", // S
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

var PAID_OPTIONS = ["Yes", "No"];
var PAYMENT_OPTIONS = ["ביט", "PayPal", "PayBox"];
var SHARE_OPTIONS = ["Yes", "No"];

/** צבעי מותג / מינוקס */
var COLOR = {
  headerBg: "#1B4332",
  headerFg: "#FFFFFF",
  stripe: "#F4F7F5",
  ink: "#0B1210",
  muted: "#5C6B64",
  gold: "#C6A15B",
  waitBit: "#E8D5F2",
  waitPaypal: "#D6EAF8",
  paid: "#D4EDDA",
  prep: "#CCE5FF",
  ship: "#1B4332",
  shipFg: "#FFFFFF",
  delivered: "#7B2D26",
  deliveredFg: "#FFFFFF",
  cancelled: "#E9ECEF",
  emptyStatus: "#F1F3F4",
  yes: "#FFE566",
  no: "#F8AD9D",
  bit: "#D6EAF8",
  paypal: "#FDEBD0",
  paybox: "#E8DAEF",
  cardBg: "#F8FAF9",
  cardBorder: "#1B4332",
};

/**
 * הרצה חד־פעמית מעורך Apps Script:
 * מעצבת את הגיליון, מוסיפה רשימות נפתחות, נוסחאות וטאבי סיכום.
 */
function setupBarberoSheet() {
  var sheet = getSheet_();
  ensureHeader_(sheet, true);
  styleSheet_(sheet);
  applyValidations_(sheet);
  applyConditionalFormat_(sheet);
  formatMoneyColumns_(sheet);
  ensureProfitFormulas_(sheet);
  setupSummarySheet_();
  setupAdsSheet_();
  setupNewsletterSheet_();
  SpreadsheetApp.flush();
}

/**
 * איפוס נתוני דמו/בדיקות — להריץ מעורך Apps Script (Run).
 * מוחק שורות נתונים בלבד; הכותרות והעיצוב נשארים.
 */
function resetBarberoDemoData() {
  var result = resetBarberoDemoData_();
  SpreadsheetApp.flush();
  Logger.log(JSON.stringify(result));
  return result;
}

function resetBarberoDemoData_() {
  var ordersCleared = clearSheetDataRows_(getSheet_(), HEADERS.length);
  var newsletterCleared = clearSheetDataRows_(
    getNewsletterSheet_(),
    NEWSLETTER_HEADERS.length,
  );
  var adsCleared = 0;
  try {
    adsCleared = clearSheetDataRows_(getAdsSheet_(), ADS_HEADERS.length);
  } catch (e) {
    adsCleared = 0;
  }

  setupBarberoSheet();

  return {
    ok: true,
    cleared: {
      orders: ordersCleared,
      newsletter: newsletterCleared,
      ads: adsCleared,
    },
  };
}

/** מוחק שורות 2…last; מחזיר כמה שורות נתונים נמחקו. */
function clearSheetDataRows_(sheet, headerWidth) {
  var last = sheet.getLastRow();
  var cleared = last >= 2 ? last - 1 : 0;
  if (last >= 2) {
    sheet.deleteRows(2, last - 1);
  }
  return cleared;
}

function doPost(e) {
  try {
    var body = JSON.parse((e && e.postData && e.postData.contents) || "{}");
    if (WEBHOOK_SECRET && body.secret !== WEBHOOK_SECRET) {
      return json_({ ok: false, error: "unauthorized" });
    }

    if (body && body.type === "track") {
      return trackOrder_(body);
    }

    if (body && body.type === "reset") {
      if (body.confirm !== "BARBERO_RESET_DEMO") {
        return json_({ ok: false, error: "confirm_required" });
      }
      return json_(resetBarberoDemoData_());
    }

    if (isNewsletterPayload_(body)) {
      return appendNewsletter_(body);
    }

    var row = body.row || {};
    var orderNumber = row.orderNumber || (body.order && body.order.number) || "";
    if (!orderNumber) {
      return json_({ ok: false, error: "missing_order_number" });
    }

    var sheet = getSheet_();
    ensureHeader_(sheet, false);

    var payment = row.payment || "ביט";
    if (payment === "Bit") payment = "ביט";
    var status =
      row.status ||
      (payment === "PayPal" ? "ממתין ל-PayPal" : "ממתין לביט");
    var paid = row.paid || "No";
    var allData = row.allData || buildAllData_(row);

    sheet.appendRow([
      status, // A
      "", // B ימי משלוח — ידני
      orderNumber, // C
      row.createdAt || formatNow_(), // D
      row.name || "", // E
      paid, // F
      payment, // G
      blankToNumber_(row.total), // H מחיר סופי
      blankToNumber_(row.productCost), // I עלות מוצר (אופציונלי מהאתר)
      blankToNumber_(row.shippingCost), // J עלות משלוח אמיתית
      "", // K רווח — נוסחה
      "", // L לשותף — נוסחה
      row.share || "No", // M
      row.items || "", // N
      allData, // O
      row.trackingNumber || "", // P
      row.shippingStatus || "", // Q
      row.phone || "", // R
      row.email || "", // S
    ]);

    var last = sheet.getLastRow();
    writeProfitFormulas_(sheet, last);
    styleDataRow_(sheet, last);
    applyValidations_(sheet);
    refreshSummarySheet_();
    return json_({ ok: true, row: last });
  } catch (err) {
    return json_({ ok: false, error: String(err && err.message ? err.message : err) });
  }
}

function buildAllData_(row) {
  var lines = [];
  if (row.phone) lines.push("טלפון: " + row.phone);
  if (row.address) lines.push("כתובת: " + row.address);
  if (row.city) lines.push("עיר: " + row.city);
  if (row.postal) lines.push("מיקוד: " + row.postal);
  if (row.unit) lines.push("דירה/קומה: " + row.unit);
  if (row.notes) lines.push("הערות: " + row.notes);
  if (row.email) lines.push("אימייל: " + row.email);
  return lines.join("\n");
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

function phoneKey_(value) {
  var digits = String(value || "").replace(/[^\d]/g, "");
  if (digits.indexOf("972") === 0 && digits.length >= 11) {
    digits = "0" + digits.slice(3);
  }
  if (digits.length > 9) digits = digits.slice(-9);
  return digits;
}

function headerIndexMap_(headers) {
  var map = {};
  for (var i = 0; i < headers.length; i++) {
    map[String(headers[i] || "").trim()] = i;
  }
  return map;
}

function extractFieldFromAllData_(text, label) {
  var raw = String(text || "");
  var re = new RegExp(label + "\\s*:\\s*([^\\n]+)");
  var m = raw.match(re);
  return m ? String(m[1] || "").trim() : "";
}

function publicTrackOrder_(row, col) {
  var status = String(row[col["סטטוס"]] || "").trim();
  var orderNumber = String(row[col["מספר הזמנה"]] || "").trim();
  var allData = col["כל הנתונים"] != null ? String(row[col["כל הנתונים"]] || "") : "";
  var city =
    (col["עיר"] != null ? String(row[col["עיר"]] || "").trim() : "") ||
    extractFieldFromAllData_(allData, "עיר");
  var items =
    (col["מוצרים"] != null ? String(row[col["מוצרים"]] || "").trim() : "") ||
    "";
  var payment =
    (col["תשלום"] != null ? String(row[col["תשלום"]] || "").trim() : "") ||
    (col["אמצעי תשלום"] != null
      ? String(row[col["אמצעי תשלום"]] || "").trim()
      : "");
  var createdAt =
    (col["תאריך"] != null ? String(row[col["תאריך"]] || "").trim() : "") ||
    (col["תאריך הזמנה"] != null
      ? String(row[col["תאריך הזמנה"]] || "").trim()
      : "");
  var shipDaysRaw =
    col["ימי משלוח"] != null
      ? row[col["ימי משלוח"]]
      : col["זמן משלוח"] != null
        ? row[col["זמן משלוח"]]
        : "";
  var shipDays =
    shipDaysRaw === "" || shipDaysRaw == null || shipDaysRaw === undefined
      ? null
      : Number(shipDaysRaw);
  if (shipDays != null && isNaN(shipDays)) shipDays = null;

  var tracking =
    col["מספר מעקב"] != null ? String(row[col["מספר מעקב"]] || "").trim() : "";
  var shippingStatus =
    col["סטטוס משלוח"] != null
      ? String(row[col["סטטוס משלוח"]] || "").trim()
      : "";

  return {
    orderNumber: orderNumber,
    status: status,
    createdAt: createdAt,
    city: city,
    items: items,
    payment: payment,
    shipDays: shipDays,
    trackingNumber: tracking || null,
    shippingStatus: shippingStatus || null,
  };
}

function trackOrder_(body) {
  var orderNumber = String(body.orderNumber || body.o || "")
    .trim()
    .toUpperCase();
  var phone = phoneKey_(body.phone || body.p || "");

  if (!orderNumber && !phone) {
    return json_({ ok: false, error: "missing_query" });
  }

  var sheet = getSheet_();
  var last = sheet.getLastRow();
  if (last < 2) {
    return json_({ ok: false, error: "not_found" });
  }

  var width = Math.max(sheet.getLastColumn(), HEADERS.length);
  var headers = sheet.getRange(1, 1, 1, width).getValues()[0];
  var col = headerIndexMap_(headers);
  if (col["מספר הזמנה"] == null || col["סטטוס"] == null) {
    return json_({ ok: false, error: "sheet_schema" });
  }

  var values = sheet.getRange(2, 1, last - 1, width).getValues();
  var matches = [];

  for (var i = 0; i < values.length; i++) {
    var row = values[i];
    var rowOrder = String(row[col["מספר הזמנה"]] || "")
      .trim()
      .toUpperCase();
    if (!rowOrder) continue;

    var rowPhone = "";
    if (col["טלפון"] != null) {
      rowPhone = phoneKey_(row[col["טלפון"]]);
    }
    if (!rowPhone && col["כל הנתונים"] != null) {
      rowPhone = phoneKey_(
        extractFieldFromAllData_(row[col["כל הנתונים"]], "טלפון"),
      );
    }

    var orderOk = orderNumber ? rowOrder === orderNumber : true;
    var phoneOk = phone ? rowPhone === phone : true;
    if (orderOk && phoneOk) {
      matches.push(publicTrackOrder_(row, col));
    }
  }

  if (!matches.length) {
    return json_({ ok: false, error: "not_found" });
  }

  var order = matches[matches.length - 1];
  return json_({
    ok: true,
    order: order,
    matchCount: matches.length,
  });
}

function doGet() {
  return json_({
    ok: true,
    service: "barbero-orders",
    sheet: SHEET_NAME,
    summary: SUMMARY_SHEET_NAME,
    ads: ADS_SHEET_NAME,
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
  sheet
    .getRange(row, 1, 1, 2)
    .setHorizontalAlignment("center")
    .setVerticalAlignment("middle");
  return json_({ ok: true, row: row });
}

function getSpreadsheet_() {
  return SpreadsheetApp.openById(SPREADSHEET_ID);
}

function getSheet_() {
  var ss = getSpreadsheet_();
  var sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) sheet = ss.insertSheet(SHEET_NAME);
  sheet.setRightToLeft(true);
  return sheet;
}

function getNewsletterSheet_() {
  var ss = getSpreadsheet_();
  var sheet = ss.getSheetByName(NEWSLETTER_SHEET_NAME);
  if (!sheet) sheet = ss.insertSheet(NEWSLETTER_SHEET_NAME);
  sheet.setRightToLeft(true);
  return sheet;
}

function getAdsSheet_() {
  var ss = getSpreadsheet_();
  var sheet = ss.getSheetByName(ADS_SHEET_NAME);
  if (!sheet) sheet = ss.insertSheet(ADS_SHEET_NAME);
  sheet.setRightToLeft(true);
  return sheet;
}

function getSummarySheet_() {
  var ss = getSpreadsheet_();
  var sheet = ss.getSheetByName(SUMMARY_SHEET_NAME);
  if (!sheet) sheet = ss.insertSheet(SUMMARY_SHEET_NAME);
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

function setupAdsSheet_() {
  var sheet = getAdsSheet_();
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(ADS_HEADERS);
  } else {
    sheet.getRange(1, 1, 1, ADS_HEADERS.length).setValues([ADS_HEADERS]);
  }
  var header = sheet.getRange(1, 1, 1, ADS_HEADERS.length);
  header.setBackground(COLOR.headerBg);
  header.setFontColor(COLOR.headerFg);
  header.setFontWeight("bold");
  header.setFontFamily("Arial");
  header.setHorizontalAlignment("center");
  header.setVerticalAlignment("middle");
  sheet.setRowHeight(1, 36);
  sheet.setFrozenRows(1);
  sheet.setColumnWidth(1, 120);
  sheet.setColumnWidth(2, 140);
  sheet.setColumnWidth(3, 110);
  sheet.setColumnWidth(4, 260);
  sheet.getRange("C2:C").setNumberFormat("₪#,##0.00");
}

/**
 * טאב סיכומים — סה״כ מכירות, עלויות, רווח נטו אחרי משלוח+מוצר+פרסום.
 */
function setupSummarySheet_() {
  var sheet = getSummarySheet_();
  sheet.clear();
  sheet.setRightToLeft(true);

  sheet.getRange("A1").setValue("סיכום רווחים — BARBERO");
  sheet.getRange("A1:B1").merge();
  sheet
    .getRange("A1")
    .setBackground(COLOR.headerBg)
    .setFontColor(COLOR.headerFg)
    .setFontWeight("bold")
    .setFontSize(16)
    .setFontFamily("Arial")
    .setHorizontalAlignment("right")
    .setVerticalAlignment("middle");
  sheet.setRowHeight(1, 44);

  var labels = [
    ["מספר הזמנות", 'COUNTA(\'הזמנות\'!C2:C)'],
    ["סה״כ מכירות (מחיר סופי)", 'SUM(\'הזמנות\'!H2:H)'],
    ["סה״כ עלות מוצרים", 'SUM(\'הזמנות\'!I2:I)'],
    ["סה״כ עלות משלוחים", 'SUM(\'הזמנות\'!J2:J)'],
    ["רווח גולמי (מכירות − מוצר − משלוח)", 'SUM(\'הזמנות\'!K2:K)'],
    ["סה״כ קידום ממומן", 'SUM(\'קידום ממומן\'!C2:C)'],
    ["רווח נטו אחרי פרסום", "B7-B8"],
    ["רווח לשותף (50%)", "B9/2"],
  ];

  // Rows 3–10 for metrics (leave row 2 as spacer)
  sheet.getRange("A2").setValue("");
  for (var i = 0; i < labels.length; i++) {
    var r = i + 3;
    sheet.getRange(r, 1).setValue(labels[i][0]);
    sheet.getRange(r, 2).setFormula("=" + labels[i][1]);
  }

  sheet.getRange("A3:A10").setFontFamily("Arial").setFontSize(11).setFontColor(COLOR.ink);
  sheet
    .getRange("B3:B10")
    .setFontFamily("Arial")
    .setFontSize(12)
    .setFontWeight("bold")
    .setHorizontalAlignment("center");

  sheet.getRange("B3").setNumberFormat("0");
  sheet.getRange("B4:B10").setNumberFormat("₪#,##0.00");

  // Highlight net profit
  sheet.getRange("A9:B9").setBackground("#D8F3DC");
  sheet.getRange("A10:B10").setBackground("#FFF3CD");

  sheet.getRange("A12").setValue("הערה: מלאו «עלות מוצר» ו«עלות משלוח» בכל שורת הזמנה — הרווח מחושב אוטומטית.");
  sheet.getRange("A12:B12").merge();
  sheet.getRange("A12").setFontColor(COLOR.muted).setFontSize(10);

  sheet.getRange("A14").setValue("סטטוסים");
  sheet.getRange("A14").setFontWeight("bold").setFontColor(COLOR.headerBg);
  sheet.getRange("A15").setValue("ממתינים לתשלום");
  sheet.getRange("B15").setFormula('=COUNTIF(\'הזמנות\'!A:A,"ממתין לביט")+COUNTIF(\'הזמנות\'!A:A,"ממתין ל-PayPal")');
  sheet.getRange("A16").setValue("שולם / בהכנה");
  sheet.getRange("B16").setFormula('=COUNTIF(\'הזמנות\'!A:A,"שולם")+COUNTIF(\'הזמנות\'!A:A,"בהכנה")');
  sheet.getRange("A17").setValue("במשלוח מארה״ב");
  sheet.getRange("B17").setFormula('=COUNTIF(\'הזמנות\'!A:A,"משלוח מארה״ב")');
  sheet.getRange("A18").setValue("נמסר");
  sheet.getRange("B18").setFormula('=COUNTIF(\'הזמנות\'!A:A,"נמסר")');

  sheet.setColumnWidth(1, 280);
  sheet.setColumnWidth(2, 160);
  sheet.setFrozenRows(1);
}

function refreshSummarySheet_() {
  try {
    setupSummarySheet_();
  } catch (e) {
    // non-fatal
  }
}

function ensureNewsletterHeader_(sheet) {
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(NEWSLETTER_HEADERS);
  } else {
    sheet.getRange(1, 1, 1, NEWSLETTER_HEADERS.length).setValues([NEWSLETTER_HEADERS]);
  }
}

function formatNow_() {
  return Utilities.formatDate(new Date(), "Asia/Jerusalem", "dd/MM/yyyy");
}

function ensureHeader_(sheet, forceRestyle) {
  var lastRow = sheet.getLastRow();
  if (lastRow === 0) {
    sheet.appendRow(HEADERS);
  } else {
    // אם הסכמה הישנה — דורסים כותרות לסכמת מינוקס (אחרי איפוס/סetup)
    sheet.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]);
    if (sheet.getMaxColumns() < HEADERS.length) {
      sheet.insertColumnsAfter(sheet.getMaxColumns(), HEADERS.length - sheet.getMaxColumns());
    }
  }
  if (forceRestyle || lastRow <= 1) {
    styleHeaderOnly_(sheet);
  }
}

function writeProfitFormulas_(sheet, row) {
  // K = H - I - J
  sheet.getRange(row, 11).setFormula("=IF(H" + row + "=\"\",\"\",H" + row + "-IF(I" + row + "=\"\",0,I" + row + ")-IF(J" + row + "=\"\",0,J" + row + "))");
  // L = K / 2
  sheet.getRange(row, 12).setFormula("=IF(K" + row + "=\"\",\"\",K" + row + "/2)");
}

function ensureProfitFormulas_(sheet) {
  var last = sheet.getLastRow();
  if (last < 2) return;
  for (var r = 2; r <= last; r++) {
    writeProfitFormulas_(sheet, r);
  }
}

function styleSheet_(sheet) {
  styleHeaderOnly_(sheet);
  sheet.setFrozenRows(1);

  var widths = [
    130, // A status
    90, // B days
    130, // C order #
    110, // D date
    120, // E name
    80, // F paid
    100, // G payment
    100, // H total
    100, // I product cost
    100, // J ship cost
    100, // K profit
    100, // L partner
    90, // M share
    200, // N items
    260, // O all data
    140, // P tracking
    200, // Q ship status
    110, // R phone
    180, // S email
  ];
  for (var i = 0; i < widths.length; i++) {
    sheet.setColumnWidth(i + 1, widths[i]);
  }

  var maxRows = Math.max(sheet.getMaxRows(), 200);
  var cols = HEADERS.length;

  if (sheet.getLastRow() > 1) {
    var data = sheet.getRange(2, 1, sheet.getLastRow() - 1, cols);
    data.setFontFamily("Arial");
    data.setFontSize(10);
    data.setVerticalAlignment("middle");
    data.setHorizontalAlignment("center");
    data.setWrap(true);
  }

  sheet.getRange(2, 1, maxRows - 1, 1).setBackground(COLOR.emptyStatus);
  formatMoneyColumns_(sheet);
  applyValidations_(sheet);
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
    sheet.getRange(row, 2, 1, HEADERS.length - 1).setBackground(COLOR.stripe);
  }
  sheet.getRange(row, 8, 1, 5).setNumberFormat("₪#,##0.00"); // H–L
  sheet.getRange(row, 15).setHorizontalAlignment("right"); // כל הנתונים
}

function formatMoneyColumns_(sheet) {
  var last = sheet.getLastRow();
  if (last < 2) return;
  sheet.getRange(2, 8, last - 1, 5).setNumberFormat("₪#,##0.00");
}

function applyValidations_(sheet) {
  var maxRows = Math.max(sheet.getMaxRows(), 200);

  var statusRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(STATUS_OPTIONS, true)
    .setAllowInvalid(false)
    .setHelpText("בחרו סטטוס הזמנה")
    .build();
  sheet.getRange(2, 1, maxRows - 1, 1).setDataValidation(statusRule);

  var paidRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(PAID_OPTIONS, true)
    .setAllowInvalid(false)
    .build();
  sheet.getRange(2, 6, maxRows - 1, 1).setDataValidation(paidRule);

  var payRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(PAYMENT_OPTIONS, true)
    .setAllowInvalid(false)
    .build();
  sheet.getRange(2, 7, maxRows - 1, 1).setDataValidation(payRule);

  var shareRule = SpreadsheetApp.newDataValidation()
    .requireValueInList(SHARE_OPTIONS, true)
    .setAllowInvalid(false)
    .build();
  sheet.getRange(2, 13, maxRows - 1, 1).setDataValidation(shareRule);
}

function applyConditionalFormat_(sheet) {
  sheet.clearConditionalFormatRules();
  var maxRows = Math.max(sheet.getMaxRows(), 500);
  var statusRange = sheet.getRange(2, 1, maxRows - 1, 1);
  var daysRange = sheet.getRange(2, 2, maxRows - 1, 1);
  var paidRange = sheet.getRange(2, 6, maxRows - 1, 1);
  var payRange = sheet.getRange(2, 7, maxRows - 1, 1);
  var shareRange = sheet.getRange(2, 13, maxRows - 1, 1);
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

  // Paid Yes/No
  rules.push(
    SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo("Yes")
      .setBackground(COLOR.yes)
      .setRanges([paidRange])
      .build(),
  );
  rules.push(
    SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo("No")
      .setBackground(COLOR.no)
      .setRanges([paidRange])
      .build(),
  );

  // Payment method colors
  rules.push(
    SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo("ביט")
      .setBackground(COLOR.bit)
      .setRanges([payRange])
      .build(),
  );
  rules.push(
    SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo("PayPal")
      .setBackground(COLOR.paypal)
      .setRanges([payRange])
      .build(),
  );
  rules.push(
    SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo("PayBox")
      .setBackground(COLOR.paybox)
      .setRanges([payRange])
      .build(),
  );

  // Profit share
  rules.push(
    SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo("Yes")
      .setBackground(COLOR.yes)
      .setRanges([shareRange])
      .build(),
  );
  rules.push(
    SpreadsheetApp.newConditionalFormatRule()
      .whenTextEqualTo("No")
      .setBackground(COLOR.no)
      .setRanges([shareRange])
      .build(),
  );

  // ימי משלוח — סולם צבעים כמו מינוקס
  rules.push(
    SpreadsheetApp.newConditionalFormatRule()
      .setGradientMinpointWithValue("#FDE2E1", SpreadsheetApp.InterpolationType.NUMBER, "5")
      .setGradientMidpointWithValue("#F8AD9D", SpreadsheetApp.InterpolationType.NUMBER, "12")
      .setGradientMaxpointWithValue("#C81D25", SpreadsheetApp.InterpolationType.NUMBER, "20")
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
