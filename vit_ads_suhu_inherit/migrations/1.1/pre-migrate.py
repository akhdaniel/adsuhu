"""One-time cleanup: reset 'failed' records that have real content but no error.

Background: generate_output_html()'s fallback used to write status='failed'
even when it successfully rendered content as plain text. The fix (v1.1)
stops new records from being falsely marked, but existing records on
production still carry the stale failed status. This migration resets them.
"""


def migrate(cr, version):
    tables = (
        "vit_product_value_analysis",
        "vit_market_mapper",
        "vit_audience_profiler",
        "vit_angle_hook",
        "vit_hook",
        "vit_ads_copy",
        "vit_image_generator",
        "vit_video_director",
        "vit_landing_page_builder",
    )
    total = 0
    for table in tables:
        cr.execute(f"""
            UPDATE {table}
            SET status = 'done'
            WHERE status = 'failed'
              AND coalesce(length(output_html), 0) > 0
              AND coalesce(trim(error_message), '') = ''
            RETURNING id
        """)
        ids = [r[0] for r in cr.fetchall()]
        if ids:
            total += len(ids)
    if total:
        print(f"[migrate 1.1] Reset {total} stale failed records across {len(tables)} tables")
