"""Off-screen pixel surfaces used to compose MiniLibX frames.

Instead of calling ``mlx_put_image_to_window`` hundreds of times per frame
(which makes the window flicker), every sprite is blitted into one in-memory
image that is sent to the window in a single call.
"""


class Surface:
    """A MiniLibX image whose pixel buffer can be read and written.

    Attributes:
        image: Raw MiniLibX image handle.
        width: Width in pixels.
        height: Height in pixels.
    """

    # In minilibx-linux a fully transparent XPM pixel has alpha 0xFF and an
    # opaque one has alpha 0x00. If transparency looks inverted on your
    # setup, change this single constant.
    TRANSPARENT_ALPHA: int = 0x00

    def __init__(
        self,
        image: object,
        buffer: memoryview,
        width: int,
        height: int,
        bytes_per_pixel: int,
        size_line: int,
        pixel_format: int,
    ) -> None:
        """Wrap an already allocated MiniLibX image.

        Args:
            image: Raw MiniLibX image handle.
            buffer: Pixel buffer returned by ``mlx_get_data_addr``.
            width: Image width in pixels.
            height: Image height in pixels.
            bytes_per_pixel: Bytes used by each pixel (bpp // 8).
            size_line: Bytes used by one image row.
            pixel_format: Endianness flag returned by MiniLibX.
        """
        self.image = image
        self.buffer = buffer
        self.width = width
        self.height = height
        self.bytes_per_pixel = bytes_per_pixel
        self.size_line = size_line
        self._alpha_offset: int = 3 if pixel_format == 0 else 0
        self._little_endian: bool = pixel_format == 0
        self._opaque: bool | None = None

    @property
    def opaque(self) -> bool:
        """Return True when no pixel is transparent (computed once)."""
        if self._opaque is None:
            self._opaque = self._compute_opaque()
        return self._opaque

    def _compute_opaque(self) -> bool:
        """Scan the alpha channel looking for transparent pixels."""
        if self.bytes_per_pixel < 4:
            return True
        row_len = self.width * self.bytes_per_pixel
        for y in range(self.height):
            start = y * self.size_line
            row = bytes(self.buffer[start:start + row_len])
            alphas = row[self._alpha_offset::self.bytes_per_pixel]
            if self.TRANSPARENT_ALPHA in alphas:
                return False
        return True

    def pixel_bytes(self, color: int) -> bytes:
        """Return one opaque pixel of colour 0xRRGGBB in this image format."""
        red = (color >> 16) & 0xFF
        green = (color >> 8) & 0xFF
        blue = color & 0xFF
        alpha = 0xFF ^ self.TRANSPARENT_ALPHA
        if self.bytes_per_pixel < 4:
            return bytes((blue, green, red))[:self.bytes_per_pixel]
        if self._little_endian:
            return bytes((blue, green, red, alpha))
        return bytes((alpha, red, green, blue))
    
    def clear(self) -> None:
        """Fill the whole surface with zeros (opaque black)."""
        size = self.size_line * self.height
        self.buffer[:size] = bytes(size)

    def copy_from(self, other: "Surface") -> None:
        """Copy every pixel from a surface with identical dimensions."""
        size = self.size_line * self.height
        self.buffer[:size] = other.buffer[:size]

    def blit(self, source: "Surface", x: int, y: int) -> None:
        """Draw ``source`` on this surface with its top-left at (x, y).

        Transparent source pixels are skipped and the drawing is clipped
        to the destination bounds.
        """
        bpp = self.bytes_per_pixel
        x_start = max(0, -x)
        x_end = min(source.width, self.width - x)
        y_start = max(0, -y)
        y_end = min(source.height, self.height - y)
        if x_start >= x_end or y_start >= y_end:
            return

        count = x_end - x_start
        row_len = count * bpp
        alpha_offset = source._alpha_offset
        transparent = self.TRANSPARENT_ALPHA
        opaque = source.opaque

        for source_y in range(y_start, y_end):
            s = source_y * source.size_line + x_start * bpp
            d = (y + source_y) * self.size_line + (x + x_start) * bpp
            row = bytes(source.buffer[s:s + row_len])

            if opaque:
                self.buffer[d:d + row_len] = row
                continue

            out = bytearray(self.buffer[d:d + row_len])
            for i in range(0, row_len, bpp):
                if row[i + alpha_offset] != transparent:
                    out[i:i + bpp] = row[i:i + bpp]
            self.buffer[d:d + row_len] = out
