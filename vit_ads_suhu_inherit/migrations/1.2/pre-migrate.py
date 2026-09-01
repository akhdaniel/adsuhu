"""One-time cleanup for a second class of stale 'failed' status.

Root cause (fixed in this version): action_split_angles()/action_split_hooks()
in angle_hook.py did unguarded dict key access (js['angles'], angle['angle'],
hook['text'], etc). If GPT returned even one malformed angle/hook, a KeyError
propagated out of the `for an in self.angle_hook_ids:` loop in
action_generate_angles(), aborting all remaining angles in that batch.
_run_background() then caught the exception at the top level and wrote
status='failed' + error_message=str(KeyError) onto the audience_profiler --
even though angles processed *before* the crash already had real content.

Unlike the 1.1 migration (which only reset records with an EMPTY error_message),
this one targets vit.audience_profiler specifically: if it's marked failed but
has at least one CHILD angle_hook with real output_html, the batch clearly made
partial/full progress and the top-level 'failed' is stale.
"""


def migrate(cr, version):
    cr.execute("""
        UPDATE vit_audience_profiler ap
        SET status = 'done'
        WHERE ap.status = 'failed'
          AND EXISTS (
              SELECT 1 FROM vit_angle_hook an
              WHERE an.audience_profiler_id = ap.id
                AND coalesce(length(an.output_html), 0) > 0
          )
        RETURNING ap.id
    """)
    ap_ids = [r[0] for r in cr.fetchall()]
    if ap_ids:
        print(f"[migrate 1.2] Reset {len(ap_ids)} audience_profiler records with stale "
              f"'failed' status that had generated angle content: {ap_ids}")

    # Same pattern one level down: angle_hook marked failed but its hooks
    # already have content (action_split_hooks partial failure).
    cr.execute("""
        UPDATE vit_angle_hook an
        SET status = 'done'
        WHERE an.status = 'failed'
          AND EXISTS (
              SELECT 1 FROM vit_hook h
              WHERE h.angle_hook_id = an.id
                AND coalesce(length(h.output_html), 0) > 0
          )
        RETURNING an.id
    """)
    an_ids = [r[0] for r in cr.fetchall()]
    if an_ids:
        print(f"[migrate 1.2] Reset {len(an_ids)} angle_hook records with stale "
              f"'failed' status that had generated hook content: {an_ids}")
