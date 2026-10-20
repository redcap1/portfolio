// edit mode (only when opened by แก้เว็บ.bat → http://localhost:.../?edit): click any text on the page to change it,
// then บันทึก writes content.js and อัปขึ้นเว็บ pushes it to GitHub. The public site never loads this file.
(function(){
const C=window.CONTENT;
// element id → where its text lives in content.js
const IDS={pHeadline:"profile.headline",pHeroL:"profile.heroLeft",pHeroR:"profile.heroRight",pAbout:"profile.about",pClients:"profile.clients",
  mail:"profile.email",pLine:"profile.line",pName:C.profile.nameTh?"profile.nameTh":"profile.name",pNameEn:"profile.name",
  pTopLabel:"sections.topLabel",pTopSub:"sections.topSub",tLong:"sections.long",tLongNote:"sections.longNote",tShort:"sections.short",
  tShortNote:"sections.shortNote",tStills:"sections.stills",stillsNote:"stillsNote" in C?"stillsNote":"sections.stillsNote",
  tGfx:"sections.graphics",tGfxNote:"sections.graphicsNote",tContact:"sections.contact",tContactNote:"sections.contactNote"};
const TABS={"s-home":"tabShowreel","s-long":"tabLong","s-short":"tabShort","s-stills":"tabStills","s-graphics":"tabGraphics","s-contact":"tabContact"};
let dirty=false;

function setPath(path,val){const ks=path.split(".");let o=C;ks.slice(0,-1).forEach(k=>{if(o[k]==null)o[k]={};o=o[k]});o[ks[ks.length-1]]=val}
function curWork(){return [...document.querySelectorAll("#workList button")].findIndex(b=>b.getAttribute("aria-current")==="true")}
function editable(el,path){
  if(!el||el.dataset.path===path)return;
  el.dataset.path=path;el.contentEditable="plaintext-only";el.spellcheck=false;el.classList.add("ed");
}
// texts inside buttons can't be typed into, so they get a box on double-click
function promptEdit(el,path){el.dataset.path=path;el.classList.add("ed","ed-dbl");el.title="ดับเบิลคลิกเพื่อแก้"}
function mark(){
  for(const id in IDS)editable(document.getElementById(id),IDS[id]);
  const k=curWork();
  if(k>=0){const i=document.getElementById("longInfo");editable(i.querySelector("h3"),`works.${k}.title`);editable(i.querySelector("p"),`works.${k}.desc`)}
  document.querySelectorAll("#stillList figcaption").forEach((f,i)=>editable(f,`stills.${i}.title`));
  document.querySelectorAll("#gfxList figcaption").forEach((f,i)=>editable(f,`graphics.${i}.title`));
  document.querySelectorAll("#shortList .sf > span:last-child").forEach((f,i)=>editable(f,`shorts.${i}.title`));
  document.querySelectorAll("#tabs .l").forEach((l,i)=>promptEdit(l,"sections."+TABS[slides[i].id]));
  document.querySelectorAll("#workList .t").forEach((t,i)=>promptEdit(t,`works.${i}.tab`));
}
function changed(el){const v=el.innerText.replace(/\s*\n\s*/g," ").trim();setPath(el.dataset.path,v);dirty=true;status("ยังไม่ได้บันทึก",true)}

document.addEventListener("input",e=>{if(e.target.dataset&&e.target.dataset.path)changed(e.target)});
document.addEventListener("keydown",e=>{if(e.key==="Enter"&&e.target.isContentEditable){e.preventDefault();e.target.blur()}},true);
// don't follow links or start videos while editing a caption
document.addEventListener("click",e=>{if(e.target.isContentEditable)e.preventDefault()},true);
document.addEventListener("dblclick",e=>{
  const el=e.target.closest(".ed-dbl");if(!el)return;e.preventDefault();
  const v=prompt("แก้ข้อความ",el.textContent);if(v==null||!v.trim())return;
  el.textContent=v.trim();changed(el);
});
new MutationObserver(mark).observe(document.body,{childList:true,subtree:true});
mark();

const css=document.createElement("style");
css.textContent=`.ed{outline:1px dashed color-mix(in srgb,currentColor 35%,transparent);outline-offset:3px;cursor:text;border-radius:2px}
.ed:hover,.ed:focus{outline:1px solid #3ea6ff}.ed-dbl{cursor:pointer}
#edBar{position:fixed;left:50%;top:10px;transform:translateX(-50%);z-index:999;display:flex;gap:8px;align-items:center;padding:6px 8px 6px 14px;
 border-radius:999px;background:rgba(20,20,22,.92);color:#eee;font:13px/1.2 system-ui,sans-serif;box-shadow:0 4px 18px rgba(0,0,0,.35)}
#edBar button{font:inherit;border:1px solid #555;background:none;color:inherit;border-radius:999px;padding:5px 12px;cursor:pointer}
#edBar button.go{background:#eee;color:#111;border-color:#eee}#edBar button:disabled{opacity:.4;cursor:default}
#edMsg.warn{color:#ffb547}`;
document.head.appendChild(css);
const bar=document.createElement("div");bar.id="edBar";
bar.innerHTML=`<b>โหมดแก้ไข</b><span id="edMsg">คลิกข้อความที่มีเส้นประเพื่อแก้</span><button id="edSave" type="button">บันทึก</button><button id="edPub" class="go" type="button">อัปขึ้นเว็บ</button>`;
document.body.appendChild(bar);
const msg=document.getElementById("edMsg");
function status(t,warn){msg.textContent=t;msg.classList.toggle("warn",!!warn)}

async function post(url,body){const r=await fetch(url,{method:"POST",headers:{"Content-Type":"application/json"},body:body&&JSON.stringify(body)});return r.json()}
async function save(){
  if(!dirty)return true;
  status("กำลังบันทึก…");
  try{const r=await post("/save",C);if(!r.ok)throw Error(r.msg);dirty=false;status("บันทึกแล้ว ✓");return true}
  catch(e){status("บันทึกไม่ได้: "+e.message,true);return false}
}
document.getElementById("edSave").onclick=save;
document.getElementById("edPub").onclick=async e=>{
  const b=e.target;if(!await save())return;
  b.disabled=true;status("กำลังอัปขึ้นเว็บ…");
  try{const r=await post("/publish");status(r.ok?"อัปแล้ว ✓ เว็บจริงจะเปลี่ยนใน 1–2 นาที":"อัปไม่ได้: "+r.msg,!r.ok)}
  catch(err){status("อัปไม่ได้ — หน้าต่างดำของ แก้เว็บ.bat ยังเปิดอยู่ไหม?",true)}
  b.disabled=false;
};
addEventListener("beforeunload",e=>{if(dirty){e.preventDefault();e.returnValue=""}});
})();
