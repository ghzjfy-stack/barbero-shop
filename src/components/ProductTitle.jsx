const keepTogether = /\d+-Star|Wet\s*\/\s*Dry/;

export default function ProductTitle({ product }) {
  const pieces = product.model.split(new RegExp(`(${keepTogether.source})`, "g"));

  return (
    <>
      {product.kind}{" "}
      <span dir="ltr">
        {pieces.map((piece, index) =>
          keepTogether.test(piece) ? (
            <span key={index} className="whitespace-nowrap">
              {piece}
            </span>
          ) : (
            piece
          ),
        )}
      </span>
    </>
  );
}
