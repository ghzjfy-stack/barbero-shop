export const announcements = [
  "100% יבוא מקורי מארה״ב",
  "משלוחים לכל הארץ (7–14 ימי עסקים)",
  "תשלום מאובטח ב-Bit או PayPal",
  "החזרה/החלפה תוך 14 ימים באריזה מקורית וסגורה בלבד",
  "אחריות ושירות ישירות מולנו",
];

export const FREE_SHIPPING = 499;
export const SHIPPING_FEE = 39;

export function shippingFeeFor(subtotal) {
  if (subtotal > 0 && subtotal < FREE_SHIPPING) return SHIPPING_FEE;
  return 0;
}

export const categories = ["הכל", "מכונות תספורת", "טרימרים ומכונות גילוח", "אביזרים ונלווים"];

export const navLinks = [
  { label: "קולקציה", href: "/#collection" },
  { label: "מכונות תספורת", href: "/#collection", category: "מכונות תספורת" },
  { label: "טרימרים ומכונות גילוח", href: "/#collection", category: "טרימרים ומכונות גילוח" },
  { label: "אביזרים ונלווים", href: "/#collection", category: "אביזרים ונלווים" },
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
    text: "אחריות מלאה ושירות מהיר לכל פנייה — ישירות מולנו.",
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
      "האחריות תקפה בהצגת חשבונית קנייה של BARBERO. השירות, המענה והטיפול מתבצעים ישירות מולנו — במהירות וללא צורך בפנייה לגורמים בחו״ל.",
    ],
  },
  faq: {
    title: "שאלות נפוצות",
    paragraphs: [
      "האם המכונה עובדת בישראל? כן. הדגמים בקטלוג הם 100V–240V ומתחברים לשקע ישראלי בלי ממיר.",
      "האם זה יבוא מקורי? כן. הסחורה מגיעה 100% מקורית מארה״ב, עם אחריות מלאה ושירות ישירות מולנו.",
      "תוך כמה זמן זה מגיע? המשלוח מגיע ישירות מארה״ב עד הבית, בדרך כלל תוך 7–14 ימי עסקים כולל מספר מעקב צמוד.",
      "אפשר להחליף דגם? כן, תוך 14 יום, כל עוד המוצר לא היה בשימוש והאריזה שמורה.",
      "איך משלמים? מקבלים תשלום בביט או ב-PayPal, אחרי אישור ההזמנה באתר.",
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
      "• כל המוצרים באתר מקוריים ומלווים באחריות מלאה ובשירות לקוחות צמוד.",
    ],
  },
};

export const products = [
  {
    id: "wahl-lithium-ss",
    kind: "טרימר",
    model: "Lithium Ion+ Stainless Steel All-in-One",
    brand: "Wahl",
    category: "טרימרים ומכונות גילוח",
    rating: 4.8,
    reviews: 38,
    sku: "BRB-W-LI-SS",
    voltage: "100V-240V (מתח אוניברסלי)",
    origin: "ארה״ב",
    badge: "חדש",
    stock: 10,
    price: 500,
    frame: "studio",
    image: "/products/wahl-lithium.jpg",
    hoverImage: "/products/wahl-lithium-kit.jpg",
    images: [
      "/products/wahl-lithium.jpg",
      "/products/wahl-lithium-kit.jpg",
      "/products/wahl-lithium-box.jpg",
      "/products/wahl-lithium-use.jpg",
    ],
    blurb:
      "טרימר All-in-One מנירוסטה לטיפוח ועיצוב זקן, עם סוללת Lithium Ion+ לעד 6 שעות עבודה. שימוש רטוב/יבש, להבים מדויקים ו־19 אורכי חיתוך לפרטים.",
    features: [
      "גוף Stainless Steel פרימיום עם מראה מקצועי ועמידות גבוהה.",
      "סוללת Lithium Ion+: עד כ־6 שעות עבודה רצופות מטעינה אחת.",
      "Wet/Dry Easy Cleanup: שימוש במקלחת או בכיור וניקוי קל במים.",
      "Precision Blades + 19 Cutting Lengths לעיצוב מדויק של זקן ופרטים.",
      "ערכת אביזרים מלאה: מסרקי Pro-Guard ממתכת, ראש Detail וראש אף/אוזן.",
      "מתח אוניברסלי 100V–240V — מתאים לחשמל בישראל.",
    ],
  },
  {
    id: "wahl-vapor",
    kind: "מכונת תספורת",
    model: "5-Star Series Vapor Cord/Cordless",
    brand: "Wahl",
    category: "מכונות תספורת",
    rating: 4.9,
    reviews: 64,
    sku: "3026480",
    voltage: "100V-240V (מתח אוניברסלי)",
    origin: "ארה״ב",
    stock: 7,
    price: 650,
    compareAt: 800,
    frame: "studio",
    image: "/products/wahl-vapor.jpg",
    hoverImage: "/products/wahl-vapor-kit.jpg",
    images: [
      "/products/wahl-vapor.jpg",
      "/products/wahl-vapor-kit.jpg",
      "/products/wahl-vapor-box.jpg",
    ],
    blurb:
      "מכונת תספורת מקצועית מסדרת 5-Star עם להב F32 FADEOUT™ לדירוגים חלקים מ־Bald עד Fade. מנוע Brushless ב־8,000 RPM, משקל קל 280g ועבודה אלחוטית עד כ־150 דקות.",
    features: [
      "להב F32 FADEOUT™: 32 שיניים עגולות (Ball-Point) לגלישה חלקה על העור ולצמצום חתכים.",
      "עיצוב פטנטי עם כ־50% יותר שיניים מלהב סטנדרטי — הזנה אחידה וחיתוך עקבי; קל בכ־6 גרם מלהב רגיל.",
      "Zero-Gap Adjustable: מעבר חלק מ־Balding ל־Fading באורך חיתוך כ־0.5–1.2 מ״מ.",
      "פלדת פחמן גבוהה עם ציפוי PVD Chrome ו־Black DLC לעמידות וחדות ממושכת.",
      "מנוע Brushless עם Adaptive Speed Control™: כ־8,000 RPM עקביים בכל סוגי השיער.",
      "סוללת ליתיום: עד כ־150 דקות עבודה אלחוטית; טעינה מלאה כ־60 דקות. אפשרות עבודה עם כבל (Cord/Cordless).",
      "משקל כ־280g — קלה יותר מ־Magic Clip®, עם אחיזה ארגונומית Non-Slip Grip.",
      "בערכה: 7 מסרקי הגבהה פרימיום (#½–#5), מסרק עיצוב לבן, שמן, מברשת ניקוי, מגן להב ומטען 5V.",
      "מתח אוניברסלי 100–240V / 50–60Hz — מתאים לחשמל בישראל.",
    ],
  },
  {
    id: "wahl-senior",
    kind: "מכונת תספורת",
    model: "Cordless Senior 5-Star",
    brand: "Wahl",
    category: "מכונות תספורת",
    rating: 4.9,
    reviews: 114,
    sku: "BRB-W-SN",
    voltage: "100V-240V (מתח אוניברסלי)",
    origin: "ארה״ב",
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
    id: "wahl-cordless-designer",
    kind: "מכונת תספורת",
    model: "Cordless Designer (#8591)",
    brand: "Wahl",
    category: "מכונות תספורת",
    rating: 4.8,
    reviews: 47,
    sku: "8591",
    voltage: "100V-240V (מתח אוניברסלי)",
    origin: "ארה״ב",
    stock: 9,
    price: 590,
    frame: "studio",
    image: "/products/wahl-cordless-designer.jpg",
    hoverImage: "/products/wahl-cordless-designer-kit.jpg",
    images: [
      "/products/wahl-cordless-designer.jpg",
      "/products/wahl-cordless-designer-features.jpg",
      "/products/wahl-cordless-designer-box.jpg",
      "/products/wahl-cordless-designer-kit.jpg",
    ],
    blurb:
      "מכונת תספורת נטענת מקצועית מסדרת הפרימיום האמריקאית של Wahl. בעלת מנוע עוצמתי ושקט, סוללת ליתיום עד 90 דקות עבודה, משקל קל במיוחד וסכין מתכווננת לדיוק מרבי. יבוא בלעדי מארה״ב.",
    features: [
      "מנוע מקצועי מהיר — עד פי 2 ממהירות מנועי Pivot סטנדרטיים, לעבודה חלקה גם בשיער עבה.",
      "להבי פלדת פחמן גבוהה (High-Carbon Steel) עמידים וחדים לאורך זמן.",
      "ידית Taper מתכווננת (Adjustable Taper Lever) לדירוג וערבוב מדויק (Fade & Blend).",
      "גוף קל ומאוזן — נוח לאחיזה ממושכת במספרה או בבית.",
      "סוללת ליתיום־יון לעבודה אלחוטית; זמן ריצה ממושך (לפי Wahl: עד כ־100 דקות).",
      "8 מסרקי הגבהה (כ־1/8״–1״) לטווח אורכים רחב.",
      "בערכה: המכונה, 8 מסרקים, מסרק עיצוב, ספק כוח/מטען, שמן, מברשת ניקוי, מגן להב אדום והוראות הפעלה.",
      "מתח אוניברסלי 100–240V — מתאים לחשמל בישראל.",
    ],
  },
  {
    id: "wahl-head-shaver",
    kind: "מכונת גילוח",
    model: "Head Shaver Kit",
    brand: "Wahl",
    category: "טרימרים ומכונות גילוח",
    rating: 4.7,
    reviews: 29,
    sku: "3032089",
    voltage: "USB (ללא מתאם בקיר)",
    origin: "Wahl",
    badge: "עמיד למים",
    stock: 10,
    price: 500,
    frame: "studio",
    image: "/products/wahl-head-shaver.jpg",
    hoverImage: "/products/wahl-head-shaver-features.jpg",
    images: [
      "/products/wahl-head-shaver.jpg",
      "/products/wahl-head-shaver-features.jpg",
      "/products/wahl-head-shaver-use.jpg",
      "/products/wahl-head-shaver-waterproof.jpg",
      "/products/wahl-head-shaver-box.jpg",
    ],
    blurb:
      "מכונת גילוח לראש ולגוף עם ארבעה להבי נירוסטה צפים לגילוח צמוד עד 0.1 מ״מ. עמידה למים בתקן IPX7 לשימוש רטוב או יבש, כולל במקלחת.",
    features: [
      "עמידות מלאה למים IPX7 — מתאימה לשימוש במקלחת ולשטיפה תחת הברז.",
      "ארבעה להבי Floating Flex מנירוסטה שמתאימים את עצמם לקווי הראש והגוף.",
      "אורך חיתוך כ־0.1 מ״מ לגילוח חלק וצמוד (Ultra-Close).",
      "סוללת ליתיום: עד כ־90 דקות עבודה אלחוטית מטעינה אחת.",
      "טעינת USB Quick Charge; זמן טעינה מלא כ־150 דקות (מתאם בקיר לא כלול).",
      "מד סוללה LED עם שלושה פסים כחולים בחזית.",
      "אחיזה ארגונומית Multi-Precision — בכף היד או באצבעות, לנוחות ושליטה.",
      "ראש גילוח נשלף לניקוי מהיר אחרי השימוש.",
      "בערכה: מכונת הגילוח, כבל USB, שמן להבים ומברשת ניקוי.",
      "מתאימה לגילוח קרקפת, חזה, כתפיים ואזורים נוספים בגוף.",
    ],
  },
  {
    id: "wahl-vanish",
    kind: "מכונת גילוח",
    model: "5-Star Series Vanish",
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
    images: ["/vanish.jpg", "/vanish-features.jpg", "/vanish-box.jpg", "/vanish-hover.jpg"],
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
    kind: "טרימר",
    model: "Aqua Blade Lithium Ion Wet / Dry",
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
    images: ["/aqua.jpg", "/aqua-kit.jpg", "/aqua-heads.jpg", "/aqua-guards.jpg", "/aqua-hover.jpg"],
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
  {
    id: "wahl-blade-oil",
    kind: "שמן להבים",
    model: "Hair Clipper Blade Oil 4 fl oz (120 ml)",
    brand: "Wahl",
    category: "אביזרים ונלווים",
    rating: 4.8,
    reviews: 210,
    sku: "03310-300A",
    voltage: "—",
    origin: "Wahl Clipper Corporation",
    badge: "משלים",
    stock: 24,
    price: 115,
    frame: "studio",
    image: "/products/wahl-blade-oil.jpg",
    hoverImage: "/products/wahl-blade-oil-howto.jpg",
    images: [
      "/products/wahl-blade-oil.jpg",
      "/products/wahl-blade-oil-howto.jpg",
      "/products/wahl-blade-oil-use.jpg",
    ],
    blurb:
      "שמן סיכה מקורי של Wahl להבי מכונות תספורת וטרימרים. כמה טיפות באופן קבוע משפרות ביצועים, מפחיתות חיכוך ומאריכות את חיי הלהבים.",
    features: [
      "נפח: 4 fl oz / 120 ml — בקבוק עם פיית מוליך מדויקת.",
      "Lubricating oil specifically prepared for clipper blades — מותאם במיוחד ללהבי Wahl.",
      "Improves Performance: מסייע לפעולה שקטה וחלקה יותר של המכונה.",
      "Extends Lifetime of Blades: מפחית חיכוך ושומר על חדות לאורך זמן.",
      "שכבת הגנה דקה נגד קורוזיה על משטחי הלהב.",
      "אופן שימוש מומלץ: 3 טיפות בחזית כל להב + טיפה בכל צד, להפעיל את המכונה ולנגב עודפים.",
      "מומלץ לשמן לפני/אחרי שימוש ולאחר ניקוי — לא להחליף ב־WD-40 או שמנים ביתיים.",
      "מתאים גם כשמן השחזה/הכנה איכותי (honing oil) לפי הנחיות היצרן.",
    ],
  },
].map((product) => ({
  ...product,
  name: `${product.kind} ${product.model}`,
}));

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
