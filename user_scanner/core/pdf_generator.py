import concurrent.futures
import io
import json
import html
from datetime import datetime
from typing import List, Any, Optional

import httpx

try:
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn  # type: ignore[import-untyped,import-not-found]
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import A4  # type: ignore[import-untyped,import-not-found]
    from reportlab.lib import colors  # type: ignore[import-untyped,import-not-found]
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # type: ignore[import-untyped,import-not-found]
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether  # type: ignore[import-untyped,import-not-found]
    from reportlab.lib.units import inch  # type: ignore[import-untyped,import-not-found]
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    from PIL import Image as PILImage  # type: ignore[import-untyped,import-not-found]
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from svglib.svglib import svg2rlg  # type: ignore[import-untyped,import-not-found]
    SVGLIB_AVAILABLE = True
except ImportError:
    SVGLIB_AVAILABLE = False


IMAGE_HEURISTIC_KEYS = ["avatar", "image", "pfp", "profile_picture", "snapcode"]


def truncate(val: Any, max_length: int = 300) -> str:
    if val is None:
        return ""
    if isinstance(val, (dict, list)):
        try:
            s = json.dumps(val)
        except Exception:
            s = str(val)
    else:
        s = str(val)

    s = "".join([c for c in s if ord(c) < 128])
    if len(s) > max_length:
        return s[:max_length] + "..."
    return s


def clean_metadata(extra: Any) -> List[tuple]:
    if not extra or not isinstance(extra, dict):
        return []
    return [(k, v) for k, v in extra.items() if not any(x in k.lower() for x in IMAGE_HEURISTIC_KEYS)]


def fetch_and_resize_image(url: str, max_size: tuple = (600, 600), timeout: float = 5.0) -> Optional[Any]:
    if not PIL_AVAILABLE:
        return None
    try:
        resp = httpx.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
            },
            timeout=timeout,
            follow_redirects=True,
        )
        if resp.status_code == 200:
            content_type = resp.headers.get("Content-Type", "")
            if SVGLIB_AVAILABLE and ("svg" in content_type.lower() or url.lower().endswith(".svg")):
                try:
                    drawing = svg2rlg(io.BytesIO(resp.content))
                    if drawing and hasattr(drawing, "width") and hasattr(drawing, "height") and drawing.width > 0 and drawing.height > 0:
                        s = min(max_size[0] / drawing.width, max_size[1] / drawing.height)
                        if s < 1.0:
                            drawing.scale(s, s)
                            drawing.width = drawing.width * s
                            drawing.height = drawing.height * s
                        return drawing
                except Exception:
                    pass

            img_raw = PILImage.open(io.BytesIO(resp.content))
            img = img_raw.convert("RGB")

            # Crop to 1:1 square
            min_dim = min(img.width, img.height)
            left = (img.width - min_dim) / 2
            top = (img.height - min_dim) / 2
            right = (img.width + min_dim) / 2
            bottom = (img.height + min_dim) / 2
            cropped = img.crop((left, top, right, bottom))

            # Scale down only if larger than max_size limit (600x600)
            if cropped.width > max_size[0] or cropped.height > max_size[1]:
                final_img = cropped.resize(max_size, PILImage.Resampling.LANCZOS)
            else:
                final_img = cropped

            img_byte_arr = io.BytesIO()
            final_img.save(img_byte_arr, format="JPEG", quality=90)
            img_byte_arr.seek(0)
            return img_byte_arr
    except Exception:
        pass
    return None


def download_images_parallel(items: List[tuple]) -> dict:
    downloaded_images: dict = {}
    if not items:
        return downloaded_images

    max_workers = min(10, max(1, len(items)))

    def _execute_downloads(progress_callback=None):
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_url = {
                executor.submit(fetch_and_resize_image, url): url
                for url, _ in items
            }
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    downloaded_images[url] = future.result()
                except Exception:
                    downloaded_images[url] = None
                if progress_callback:
                    progress_callback()

    if RICH_AVAILABLE:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            transient=True,
        ) as progress:
            task_id = progress.add_task("[cyan]Downloading profile media...", total=len(items))
            _execute_downloads(progress_callback=lambda: progress.advance(task_id))
    else:
        _execute_downloads()

    return downloaded_images


def generate_pdf_report(
    target: str,
    scan_type: str,
    results: List[Any],
    total_modules: Optional[int] = None,
    include_media: bool = True,
    version: Optional[str] = None,
) -> bytes:
    if not REPORTLAB_AVAILABLE:
        raise ImportError(
            "ReportLab is required for PDF generation. "
            "Please install it using: pip install user-scanner[pdf] or pip install reportlab pillow svglib"
        )

    # Convert Result objects to dicts if needed
    raw_results = []
    for r in results:
        if hasattr(r, "to_dict"):
            raw_results.append(r.to_dict())
        elif isinstance(r, dict):
            raw_results.append(r)

    if total_modules is None:
        total_modules = len(raw_results)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )

    styles = getSampleStyleSheet()

    header_brand_style = ParagraphStyle(
        "HeaderBrand",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#555555"),
        fontName="Helvetica-Bold",
    )
    header_title_style = ParagraphStyle(
        "HeaderTitle",
        parent=styles["Normal"],
        fontSize=18,
        leading=22,
        textColor=colors.black,
        fontName="Helvetica-Bold",
    )
    header_subtitle_style = ParagraphStyle(
        "HeaderSubtitle",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#555555"),
        fontName="Helvetica",
    )
    date_right_style = ParagraphStyle(
        "DateRight",
        parent=styles["Normal"],
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#666666"),
        alignment=2,  # Right align
    )
    section_title_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        textColor=colors.black,
        spaceBefore=15,
        spaceAfter=10,
        fontName="Helvetica-Bold",
    )
    normal_style = styles["Normal"]

    elements = []
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    version_str = f" v{version}" if version else ""

    header_left = [
        Paragraph(f"User Scanner{version_str.lower()}", header_brand_style),
        Spacer(1, 2),
        Paragraph("INTELLIGENCE DOSSIER", header_title_style),
        Spacer(1, 2),
        Paragraph("AUTOMATED OSINT EXTRACTION", header_subtitle_style),
    ]

    header_right = [
        Paragraph(
            "<font size=9 color='#dc2626' name='Helvetica-Bold'>CONFIDENTIAL / INTERNAL</font><br/>"
            + date_str,
            date_right_style,
        )
    ]

    # Header Table
    header_data = [[header_left, header_right]]
    header_table = Table(header_data, colWidths=[4.2 * inch, 2.8 * inch])
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                ("LINEBELOW", (0, 0), (-1, -1), 1, colors.HexColor("#222222")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(header_table)
    elements.append(Spacer(1, 20))

    hits = [
        r
        for r in raw_results
        if str(r.get("status", "")).lower() in ["found", "registered", "taken"]
    ]

    # Summary Box
    summary_data = [
        [
            Paragraph(
                f"<font size=7 color='#6b7280'>SUBJECT TARGET</font><br/><font size=10 name='Helvetica-Bold'>{html.escape(str(target))}</font>",
                normal_style,
            ),
            Paragraph(
                f"<font size=7 color='#6b7280'>SCAN PARAMETER</font><br/><font size=10 name='Helvetica-Bold'>{html.escape(scan_type.upper())}</font>",
                normal_style,
            ),
            Paragraph(
                f"<font size=7 color='#6b7280'>DATE OF REPORT</font><br/><font size=10 name='Helvetica-Bold'>{html.escape(date_str)}</font>",
                normal_style,
            ),
            Paragraph(
                f"<font size=7 color='#6b7280'>TOTAL FINDINGS</font><br/><font size=10 name='Helvetica-Bold'>{len(hits)} Hits across {total_modules} vectors</font>",
                normal_style,
            ),
        ]
    ]
    summary_table = Table(summary_data, colWidths=[1.8 * inch] * 4)
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fafafa")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#e5e7eb")),
                ("PADDING", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    elements.append(summary_table)

    # Profile Photos Grid
    if include_media and PIL_AVAILABLE:
        unique_photos = {}
        for idx, hit in enumerate(hits):
            media = hit.get("media", {})
            extra = hit.get("extra", {})
            
            urls: List[str] = []
            
            if isinstance(media, dict) and media:
                urls.extend(str(v) for v in media.values() if v)
            elif isinstance(extra, dict) and extra:
                for k, v in extra.items():
                    if v and isinstance(v, str):
                        k_lower = k.lower()
                        if any(x in k_lower for x in IMAGE_HEURISTIC_KEYS):
                            urls.append(v)
                            
            for url in urls:
                if url and isinstance(url, str) and url.startswith("http") and url not in unique_photos:
                    unique_photos[url] = {
                        "site": hit.get("site_name", "Unknown"),
                        "slNo": idx + 1,
                    }

        if unique_photos:
            items = list(unique_photos.items())
            downloaded_images = download_images_parallel(items)

            photo_cells = []
            for url, info in items:
                img_io_or_drawing = downloaded_images.get(url)
                if img_io_or_drawing:
                    if isinstance(img_io_or_drawing, io.BytesIO):
                        rl_img = RLImage(img_io_or_drawing, width=60, height=60)
                    else:
                        # For SVGs, we must scale the layout drawing itself to 60x60
                        drawing = img_io_or_drawing
                        if hasattr(drawing, "width") and hasattr(drawing, "height") and drawing.width > 0 and drawing.height > 0:
                            s = min(60.0 / drawing.width, 60.0 / drawing.height)
                            drawing.scale(s, s)
                            drawing.width = drawing.width * s
                            drawing.height = drawing.height * s
                        rl_img = drawing
                    caption = Paragraph(
                        f"<font size=6 color='#6b7280'>{info['slNo']}. {html.escape(str(info['site']))}</font>",
                        ParagraphStyle("c", alignment=1),
                    )
                    photo_cells.append([rl_img, caption])

            if photo_cells:
                elements.append(
                    Paragraph("IDENTIFIED PROFILE MEDIA", section_title_style)
                )
                row = []
                grid_data = []
                for cell in photo_cells:
                    cell_table = Table(
                        [[cell[0]], [cell[1]]], colWidths=[65], rowHeights=[65, 15]
                    )
                    cell_table.setStyle(
                        TableStyle(
                            [
                                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                (
                                    "BOX",
                                    (0, 0),
                                    (0, 0),
                                    1,
                                    colors.HexColor("#e5e7eb"),
                                ),
                                (
                                    "BACKGROUND",
                                    (0, 0),
                                    (0, 0),
                                    colors.HexColor("#f3f4f6"),
                                ),
                            ]
                        )
                    )
                    row.append(cell_table)
                    if len(row) == 7:
                        grid_data.append(row)
                        row = []
                if row:
                    while len(row) < 7:
                        row.append("")
                    grid_data.append(row)

                grid_table = Table(grid_data)
                grid_table.setStyle(
                    TableStyle(
                        [
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ]
                    )
                )
                elements.append(grid_table)
                elements.append(Spacer(1, 10))

    # Footprint Table
    elements.append(Paragraph("DIGITAL FOOTPRINT MAPPING", section_title_style))

    is_cross_scan = "cross" in scan_type.lower()

    if is_cross_scan:
        table_data = [
            [
                Paragraph(
                    "<font size=8 name='Helvetica-Bold' color='#374151'>SL</font>",
                    normal_style,
                ),
                Paragraph(
                    "<font size=8 name='Helvetica-Bold' color='#374151'>TARGET</font>",
                    normal_style,
                ),
                Paragraph(
                    "<font size=8 name='Helvetica-Bold' color='#374151'>PLATFORM</font>",
                    normal_style,
                ),
                Paragraph(
                    "<font size=8 name='Helvetica-Bold' color='#374151'>CATEGORY</font>",
                    normal_style,
                ),
                Paragraph(
                    "<font size=8 name='Helvetica-Bold' color='#374151'>STATUS</font>",
                    normal_style,
                ),
                Paragraph(
                    "<font size=8 name='Helvetica-Bold' color='#374151'>IDENTIFIED URL</font>",
                    normal_style,
                ),
            ]
        ]
    else:
        table_data = [
            [
                Paragraph(
                    "<font size=8 name='Helvetica-Bold' color='#374151'>SL</font>",
                    normal_style,
                ),
                Paragraph(
                    "<font size=8 name='Helvetica-Bold' color='#374151'>PLATFORM</font>",
                    normal_style,
                ),
                Paragraph(
                    "<font size=8 name='Helvetica-Bold' color='#374151'>CATEGORY</font>",
                    normal_style,
                ),
                Paragraph(
                    "<font size=8 name='Helvetica-Bold' color='#374151'>STATUS</font>",
                    normal_style,
                ),
                Paragraph(
                    "<font size=8 name='Helvetica-Bold' color='#374151'>IDENTIFIED URL</font>",
                    normal_style,
                ),
            ]
        ]

    for idx, hit in enumerate(hits):
        status = str(hit.get("status", "Unknown"))
        status_color = (
            "#16a34a"
            if status.lower() in ["found", "registered", "taken"]
            else "#111111"
        )
        url_text = truncate(hit.get("url", "N/A"), 100)
        target_val = html.escape(str(hit.get("email") or hit.get("username") or ""))

        if is_cross_scan:
            table_data.append(
                [
                    Paragraph(
                        f"<font size=8>{idx + 1}</font>",
                        ParagraphStyle("C", alignment=1),
                    ),
                    Paragraph(
                        f"<font size=8>{target_val}</font>", normal_style
                    ),
                    Paragraph(
                        f"<font size=8>{html.escape(str(hit.get('site_name', '')))}</font>", normal_style
                    ),
                    Paragraph(
                        f"<font size=8>{html.escape(str(hit.get('category', '')))}</font>", normal_style
                    ),
                    Paragraph(
                        f"<font size=8 color='{status_color}'>{html.escape(status)}</font>",
                        normal_style,
                    ),
                    Paragraph(
                        f"<font size=7 color='#2563eb'>{html.escape(url_text)}</font>", normal_style
                    ),
                ]
            )
        else:
            table_data.append(
                [
                    Paragraph(
                        f"<font size=8>{idx + 1}</font>",
                        ParagraphStyle("C", alignment=1),
                    ),
                    Paragraph(
                        f"<font size=8>{html.escape(str(hit.get('site_name', '')))}</font>", normal_style
                    ),
                    Paragraph(
                        f"<font size=8>{html.escape(str(hit.get('category', '')))}</font>", normal_style
                    ),
                    Paragraph(
                        f"<font size=8 color='{status_color}'>{html.escape(status)}</font>",
                        normal_style,
                    ),
                    Paragraph(
                        f"<font size=7 color='#2563eb'>{html.escape(url_text)}</font>", normal_style
                    ),
                ]
            )

    if is_cross_scan:
        data_table = Table(
            table_data,
            colWidths=[0.4 * inch, 1.5 * inch, 1.2 * inch, 0.9 * inch, 0.9 * inch, 2.4 * inch],
            repeatRows=1,
        )
    else:
        data_table = Table(
            table_data,
            colWidths=[0.5 * inch, 1.5 * inch, 1.2 * inch, 1.0 * inch, 3.1 * inch],
            repeatRows=1,
        )
    data_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#e5e7eb")),
                ("INNERGRID", (0, 0), (-1, -1), 1, colors.HexColor("#e5e7eb")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
                ("TOPPADDING", (0, 0), (-1, 0), 5),
            ]
        )
    )
    elements.append(data_table)

    # Deep Metadata Cards
    hits_with_meta = []
    for hit in hits:
        meta = clean_metadata(hit.get("extra"))
        media = hit.get("media")
        if media and isinstance(media, dict):
            for k, v in media.items():
                if v:
                    meta.append((k, v))
        if meta:
            hits_with_meta.append((hit, meta))

    if hits_with_meta:
        elements.append(
            Paragraph("EXTRACTED DEEP INTELLIGENCE", section_title_style)
        )

        for hit, meta in hits_with_meta:
            site_title = html.escape(str(hit.get('site_name', '')))
            target_val = html.escape(str(hit.get("email") or hit.get("username") or ""))
            if is_cross_scan and target_val:
                site_title += f" ({target_val})"

            meta_elements = [
                Paragraph(
                    f"<font size=10 name='Helvetica-Bold'>{site_title}</font>",
                    normal_style,
                ),
                Spacer(1, 5),
            ]

            meta_grid = []
            row = []
            for k, v in meta:
                key_para = f"<font size=7 color='#6b7280'>{html.escape(str(k).replace('_', ' ').upper())}</font>"
                val_para = (
                    f"<font size=8 color='#1f2937'>{html.escape(truncate(v, 200))}</font>"
                )
                cell = Paragraph(f"{key_para}<br/>{val_para}", normal_style)
                row.append(cell)
                if len(row) == 2:
                    meta_grid.append(row)
                    row = []
            if row:
                row.append("")
                meta_grid.append(row)

            if meta_grid:
                m_table = Table(meta_grid, colWidths=[3.6 * inch, 3.6 * inch])
                m_table.setStyle(
                    TableStyle(
                        [
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ]
                    )
                )
                meta_elements.append(m_table)

            block_table = Table([[meta_elements]], colWidths=[7.2 * inch])
            block_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f9fafb")),
                        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#f3f4f6")),
                        ("PADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                    ]
                )
            )

            elements.append(KeepTogether(block_table))
            elements.append(Spacer(1, 10))

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()
