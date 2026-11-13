from pathlib import Path
import streamlit as st
from PIL import Image
from reports import load_run,heatmap,grid_image,asset,save_review,index_reviews,filter_findings,overlay_image,export_html,DECISIONS

st.set_page_config(page_title='Inspection evidence',layout='wide')
st.title('Inspection evidence review')
if st.session_state.get('review-notice'):st.success(st.session_state.pop('review-notice'))
run=st.text_input('Run directory','outputs/demo')
try:
    root,metadata,rows=load_run(run)
    st.caption(f"Run status: {metadata.get('status','legacy / unknown')} · synthetic: {metadata.get('synthetic','unknown')}")
    if metadata.get('status')!='completed': st.warning('Run completion is not verified. Inspect its metadata before drawing conclusions.')
    findings=[row for row in rows if row.get('suspicious')]
    index=index_reviews(root,findings)
    mode=st.selectbox('Review filter',['All','Unreviewed','Conflicting','Stale'],key='review-filter')
    candidates=filter_findings(rows,index,mode)
    st.caption(f"{len(candidates)} shown · {sum(not x['valid'] for x in index.values())} unreviewed · {sum(x['conflicting'] for x in index.values())} conflicting")
    if not candidates: st.info('No findings match this review filter.'); st.stop()
    frame=st.selectbox('Frame',[row['frame'] for row in candidates],key='frame-choice')
    row=next(row for row in candidates if row['frame']==frame)
    st.write(f"Timestamp {row['timestamp_s']:.3f}s · score {row.get('max_score')}")
    columns=st.columns(2)
    columns[0].image(grid_image(heatmap(root,row)),caption='Compact score heatmap')
    if row.get('evidence'):
        evidence=st.selectbox('Evidence image',row['evidence'],key=f'evidence-{root}-{frame}')
        show_overlay=st.checkbox('Overlay score heatmap',key=f'overlay-{root}-{frame}')
        if show_overlay:
            try:columns[1].image(overlay_image(root,row,evidence),caption='Full-frame score overlay')
            except ValueError as exc:columns[1].info(str(exc))
        else:
            with Image.open(asset(root,evidence)) as image: columns[1].image(image.copy(),caption='Retained evidence')
    else: columns[1].info('No evidence retained for this frame.')
    reviewer=st.text_input('Reviewer name')
    decision=st.selectbox('Decision',DECISIONS,index=2,key=f'decision-{root}-{frame}-{index[frame]["binding"]}')
    notes=st.text_area('Notes',key=f'notes-{root}-{frame}-{index[frame]["binding"]}')
    if st.button('Save review',disabled=not reviewer.strip(),key='save-review'):
        saved=save_review(root,row,decision,reviewer,notes)
        st.session_state['review-notice']=f"Saved {decision.replace('_',' ')} for frame {frame} at {row['timestamp_s']:.3f}s"
        st.rerun()
    fresh=index_reviews(root,[row])[frame];valid,stale=fresh['valid'],fresh['stale']
    st.caption(f'{len(valid)} valid reviews · {len(stale)} stale reviews')
    if fresh['conflicting']:st.warning('Reviewers disagree on this finding. Resolve the conflict before making a final assessment.')
    for review in valid:
        st.write(f"{review['decision'].replace('_',' ').capitalize()} — {review['reviewer']}")
        if review.get('notes'):st.write(review['notes'])
    with st.expander('Review audit details'):st.json({'valid_reviews':valid,'stale_reviews':len(stale)})
    if st.button('Export HTML report'):
        import uuid
        output=export_html(root,root/f'report-{uuid.uuid4().hex[:8]}.html')
        st.download_button('Download report',output.read_bytes(),file_name=output.name,mime='text/html')
except (OSError,ValueError,KeyError) as exc: st.error(str(exc))
