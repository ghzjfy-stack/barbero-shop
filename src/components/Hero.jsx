export const announcements = [
  "100% יבוא מקורי מארה״ב",
  "משלוחים לכל הארץ (7–14 ימי עסקים)",
  "תשלום מאובטח ב-Bit",
  "החזרה/החלפה תוך 14 ימים באריזה מקורית וסגורה בלבד",
  "אחריות ושירות לקוחות בעברית",
];

export const FREE_SHIPPING = 499;
export const SHIPPING_FEE = 39;

export function shippingFeeFor(subtotal) {
  if (subtotal > 0 && subtotal < FREE_SHIPPING) return SHIPPING_FEE;
  return 0;
}

export const categories = ["הכל", "מכונות תספורת", "טרימרים ומכונות גילוח"];

export const navLinks = [
  { label: "קולקציה", href: "/#collection" },
  { label: "מכונות תספורת", href: "/#collection", category: "מכונות תספורת" },
  { label: "טרימרים ומכונות גילוח", href: "/#collection", category: "טרימרים ומכונות גילוח" },
  { label: "אודות", href: "/about" },
];

export const trustItems = [
  {
    icon: "truck",
    title: "משלוח בינלאומי",
    text: "משלוח ישיר מארה״ב עד הבית, בדרך כלל תוך 7–14 ימי עסקים כולל מספר מעקב.",
  },
  {
    icon: "box",
    title: "אריזה מקורית",
    text: "מוצרים חדשים באריזה מקורית וסגורה מהיצרן.",
  },
  {
    icon: "globe",
    title: "יבוא ישיר מארה״ב",
    text: "ציוד מקורי בלבד, המיובא ישירות מהמותג בארה״ב. 100% מוצרים מקוריים, חדשים ובאריזה סגורה.",
  },
  {
    icon: "shield",
    title: "אחריות ושירות",
    text: "אחריות מלאה ושירות לקוחות בעברית לכל פנייה.",
  },
];

export const serviceLinks = [
  { label: "מעקב הזמנה", page: "tracking" },
  { label: "משלוחים והחזרות", page: "shipping" },
  { label: "אחריות", page: "warranty" },
  { label: "שאלות נפוצות", page: "faq" },
  { label: "מדיניות פרטיות", page: "privacy" },
  { label: "תקנון", page: "terms" },
];

export const pages = {
  tracking: {
    title: "מעקב הזמנה",
    paragraphs: [
      "הזינו את מספר ההזמנה ממסך האישור. המעקב בדמו הזה נשמר בדפדפן בלבד.",
    ],
  },
  shipping: {
    title: "משלוחים והחזרות",
    paragraphs: [
      "משלוח לכל הארץ תוך 7–14 ימי עסקים.",
      "משלוח חינם בקנייה מעל 499 ₪! בהזמנות מתחת לסכום זה, עלות המשלוח הינה 39 ₪.",
      "החזרה או החלפה ניתן לבצע תוך 14 ימים מיום קבלת המוצר, כשהפריט באריזתו המקורית והסגורה בלבד ולא נעשה בו כל שימוש. מטעמי היגיינה, מוצרים שנפתחו אינם ניתנים להחזרה.",
      "האתר מספק שירות במשלוחים לכל הארץ (ללא איסוף עצמי).",
    ],
  },
  warranty: {
    title: "אחריות ושירות BARBERO",
    paragraphs: [
      "כל מכונות התספורת, הפיניש ומכונות הגילוח מגיעות עם אחריות יבואן ל-12 חודשים על המנוע והרכיבים החשמליים (בלאי טבעי של להבים, סכינים ורשתות אינו כלול).",
      "האחריות תקפה בהצגת חשבונית קנייה של BARBERO. השירות, המענה והטיפול מתבצעים ישירות מול צוות השירות שלנו בעברית, במהירות וללא צורך בפנייה לגורמים בחו״ל.",
    ],
  },
  faq: {
    title: "שאלות נפוצות",
    paragraphs: [
      "האם המכונה עובדת בישראל? כן. הדגמים בקטלוג הם 100V–240V ומתחברים לשקע ישראלי בלי ממיר.",
      "האם זה יבוא מקורי? כן. הסחורה מגיעה 100% מקורית מארה״ב, עם אחריות מלאה שלנו ושירות לקוחות בעברית.",
      "תוך כמה זמן זה מגיע? המשלוח מגיע ישירות מארה״ב עד הבית, בדרך כלל תוך 7–14 ימי עסקים כולל מספר מעקב צמוד.",
      "אפשר להחליף דגם? כן, תוך 14 יום, כל עוד המוצר לא היה בשימוש והאריזה שמורה.",
      "איך משלמים? כרגע מקבלים תשלום בביט בלבד.",
    ],
  },
  privacy: {
    title: "מדיניות פרטיות",
    paragraphs: [
      "אנו ב-BARBERO מחויבים לשמירה מלאה על פרטיותכם. הפרטים האישיים משמשים אך ורק לצורך עיבוד המשלוח. כל פעולות התשלום מבוצעות בסליקה מוצפנת ומאובטחת (SSL) ואינן נשמרות בשרת. איננו מעבירים מידע לגורם שלישי.",
    ],
  },
  terms: {
    title: "תקנון",
    paragraphs: [
      "ברוכים הבאים ל-BARBERO. האתר מציע ציוד תספורת וגילוח מקורי ביבוא ישיר מארה״ב.",
      "• כל ההזמנות מטופלות ונשלחות ישירות לבית הלקוח תוך 7–14 ימי עסקים.",
      "• ניתן להחזיר או להחליף מוצר תוך 14 יום באריזתו המקורית ושלא נעשה בו שימוש.",
      "• כל המוצרים באתר מקוריים ומלווים באחריות מלאה ובשירות לקוחות בעברית.",
    ],
  },
};

export const products = [
  {
    id: "wahl-senior",
    name: "מכונת תספורת Wahl Cordless Senior 5-Star",
    brand: "Wahl",
    category: "מכונות תספורת",
    rating: 4.9,
    reviews: 114,
    sku: "BRB-W-SN",
    voltage: "100V-240V (מתח אוניברסלי)",
    origin: "ארה״ב",
    badge: "חדש",
    stock: 8,
    price: 550,
    frame: "studio",
    image: "/products/wahl-senior.webp",
    hoverImage: "/products/wahl-senior-use.webp",
    images: [
      "/products/wahl-senior.webp",
      "/products/wahl-senior-use.webp",
      "/products/wahl-senior-hero.webp",
    ],
    blurb:
      "מכונת תספורת אלחוטית מקצועית מסדרת 5-Star. גוף מתכת מחוזק, מנוע עוצמתי ולהב מבוקש לדירוגים מדויקים (Fade). אחיזה נוחה וארגונומית לעבודה ממושכת.",
  },
  {
    id: "fast-feed",
    name: "מכונת תספורת Wahl 5-Star Detailer Li",
    brand: "Wahl",
    category: "טרימרים ומכונות גילוח",
    rating: 4.6,
    reviews: 88,
    sku: "BRB-W-DL",
    voltage: null,
    origin: "ארה״ב",
    badge: null,
    stock: 0,
    price: 499,
    frame: "studio",
    image:
      "https://images.unsplash.com/photo-1493256338651-d82f7acb2b38?auto=format&fit=crop&w=1000&q=80",
    blurb:
      "דיטיילר אלחוטי מסדרת 5-Star, לקווים חדים ולעבודה צמודה. אזלה מהמלאי כרגע — אפשר לשמור אותה למועדפים שלי.",
  },
  {
    id: "wahl-vanish",
    name: "Wahl 5-Star Series Vanish Shaver",
    brand: "Wahl",
    category: "טרימרים ומכונות גילוח",
    rating: 4.8,
    reviews: 56,
    sku: "8173-700",
    voltage: "100V-240V (מתח אוניברסלי)",
    origin: "ארה״ב",
    badge: "Zero Finish",
    stock: 8,
    price: 420,
    compareAt: 520,
    frame: "studio",
    image: "/vanish.jpg",
    hoverImage: "/vanish-hover.jpg",
    images: ["/vanish.jpg", "/vanish-hover.jpg"],
    blurb:
      "מכונת גילוח רשת כפולה מקצועית להחלקה מלאה (Zero Finish), עיצוב קווי צוואר וזקן, וגילוח קרקפת חלק ללא גירויים.",
    features: [
      "מערכת חיתוך עצמאית (Independent Cutter Bars): להבים ורשתות זזים בנפרד להתאמה מושלמת לתווי הפנים והקרקפת.",
      "רשתות זהב היפואלרגניות (Micro-Thin Gold Foils): גילוח קרוב במיוחד ללא צריבה או גירויים בעור.",
      "סוללת ליתיום-יון עוצמתית: מעל 100+ דקות עבודה רצופות מטעינה אחת.",
      "חיווי סוללה חכם (LED Fuel Gauge): 3 פסי תאורה כחולים בחזית המציגים את מצב הסוללה בזמן אמת.",
      "מנגנון נעילת נסיעות (Travel Lock): מונע הפעלה מקרית של המכשיר בדרכים.",
      "מתח אוניברסלי (100V-240V): מתאים לחשמל בישראל (עבודה נטענת או עם כבל).",
    ],
  },
  {
    id: "wahl-aqua",
    name: "Wahl Aqua Blade Lithium Ion Wet / Dry Trimmer",
    brand: "Wahl",
    category: "טרימרים ומכונות גילוח",
    rating: 4.7,
    reviews: 42,
    sku: "9899-100",
    voltage: "100V-240V (מתח אוניברסלי)",
    origin: "ארה״ב",
    badge: "עמיד למים",
    stock: 8,
    price: 500,
    compareAt: 620,
    frame: "studio",
    image: "/aqua.jpg",
    hoverImage: "/aqua-hover.jpg",
    images: ["/aqua.jpg", "/aqua-hover.jpg"],
    blurb:
      "מכונת טיפוח ועיצוב זקן וגוף עמידה במים לחלוטין (100% Waterproof), עם להבי פלדה קרובים במיוחד לשימוש במקלחת ובשטיפה מלאה תחת הברז.",
    features: [
      "100% עמידות למים (Showerproof): עבודה רטובה ויבשה (Wet/Dry) לניקוי מהיר תחת הברז או לשימוש נוח במקלחת.",
      "להב Extreme Precision Blade: להב נירוסטה המיוצר בארה״ב החותך כ-60% קרוב יותר מלהבי טרימר רגילים (Ultra-Close Cutting).",
      "סוללת ליתיום-יון עוצמתית: מספקת עד 180 דקות עבודה (3 שעות!) מטעינה מלאה, כולל טעינה מהירה של דקה לשימוש דחוף.",
      "אחיזת סיליקון ארגונומית (Non-Slip Grip): מארז סיליקון נגד החלקה לאחיזה יציבה ובטוחה בסביבה רטובה.",
      "ערכת טיפוח מקיפה: כוללת מסרקי הגבהה מגוונים לעיצוב הזקן והגוף בדרגות שונות.",
      "מתח אוניברסלי (100V-240V): תומך בחשמל בישראל לטעינה בטוחה ומהירה.",
    ],
  },
];

export function formatPrice(value) {
  const amount = new Intl.NumberFormat("he-IL", { maximumFractionDigits: 0 }).format(value);
  return `₪${amount}`;
}

export function findProduct(id) {
  return products.find((product) => product.id === id) ?? null;
}

export function resolveOffer(product, variantId) {
  const variant =
    product.variants?.find((item) => item.id === variantId) ||
    product.variants?.[0] ||
    null;

  if (variant) {
    return {
      variant,
      price: variant.price,
      compareAt: variant.compareAt ?? null,
      label: variant.label,
    };
  }

  return {
    variant: null,
    price: product.price,
    compareAt: product.compareAt ?? null,
    label: null,
  };
}

export function discountPercent(price, compareAt) {
  if (!compareAt || compareAt <= price) return 0;
  return Math.round((1 - price / compareAt) * 100);
}

export function fromPrice(product) {
  if (product.variants?.length) {
    return Math.min(...product.variants.map((variant) => variant.price));
  }
  return product.price;
}
