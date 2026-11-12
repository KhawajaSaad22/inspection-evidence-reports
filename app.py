from pathlib import Path
import streamlit as st
from PIL import Image
from reports import load_run,heatmap,grid_image,asset,save_review,reviews_for,export_html,DECISIONS

st.set_page_config(page_title='Inspection evidence',layout='wide')
st.title('Inspection evidence review')
run=st.text_input('Run directory','outputs/demo')
try:
    root,metadata,rows=load_run(run)
    st.caption(f"Run status: {metadata.get('status','legacy / unknown')} · synthetic: {metadata.get('synthetic','unknown')}")
    if metadata.get('status')!='completed': st.warning('Run completion is not verified. Inspect its metadata before drawing conclusions.')
    candidates=[row for row in rows if row.get('suspicious')]
    if not candidates: st.info('No suspicious frames in this run.'); st.stop()
    frame=st.selectbox('Frame',[row['frame'] for row in candidates])
    row=next(row for row in candidates if row['frame']==frame)
    st.write(f"Timestamp {row['timestamp_s']:.3f}s · score {row.get('max_score')}")
    columns=st.columns(2)
    columns[0].image(grid_image(heatmap(root,row)),caption='Compact score heatmap')
    if row.get('evidence'):
        with Image.open(asset(root,row['evidence'][0])) as image: columns[1].image(image.copy(),caption='Retained evidence')
    else: columns[1].info('No evidence retained for this frame.')
    reviewer=st.text_input('Reviewer name'); decision=st.selectbox('Decision',DECISIONS)
    notes=st.text_area('Notes',key=f'notes-{root}-{frame}')
    if st.button('Save review',disabled=not reviewer.strip()):
        saved=save_review(root,row,decision,reviewer,notes); st.success(f'Review saved: {saved.name}')
    valid,stale=reviews_for(root,row)
    st.write({'valid_reviews':valid,'stale_reviews':len(stale)})
    if st.button('Export HTML report'):
        import uuid
        output=export_html(root,root/f'report-{uuid.uuid4().hex[:8]}.html')
        st.download_button('Download report',output.read_bytes(),file_name=output.name,mime='text/html')
except (OSError,ValueError,KeyError) as exc: st.error(str(exc))
