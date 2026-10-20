// edit mode (only when opened by แก้เว็บ.bat → http://localhost:.../?edit): click any text on the page to change it,
// buttons on videos/pictures swap the file, then บันทึก writes content.js and อัปขึ้นเว็บ pushes it to GitHub.
// The public site never loads this file.
(function(){
const C=window.CONTENT;
// element id → where its text lives in content.js
const IDS={pHeadline:"profile.headline",pHeroL:"profile.heroLeft",pHeroR:"profile.heroRight",pAbout:"profile.about",pClients:"profile.clients",
  mail:"profile.email",pLine:"profile.line",pName:C.profile.nameTh?"profile.nameTh":"profile.name",pNameEn:"profile.name",
  pTopLabel:"sections.topLabel",pTopSub:"sections.topSub",tLong:"sections.long",tLongNote:"sections.longNote",tShort:"sections.short",
  tShortNote:"sections.shortNote",tStills:"sections.stills",stillsNote:"stillsNote" in C?"stillsNote":"sections.stillsNote",
  tGfx:"sections.graphics",tGfxNote:"sections.graphicsNote",tContact:"sections.contact",tContactNote:"sections.contactNote"};
const TABS={"s-home":"tabShowreel","s-long":"tabLong","s-short":"tabShort","s-stills":"tabStills","s-graphics":"tabGraphics","s-contact":"tabContact"};
const ytId=s=>{const m=(s||"").match(/(?:v=|youtu\.be\/|shorts\/|embed\/|live\/)([\w-]{11})/);return m?m[1]:/^[\w-]{11}$/.test(s||"")?s:""};
let dirty=false;

function setPath(path,val){const ks=path.split(".");let o=C;ks.slice(0,-1).forEach(k=>{if(o[k]==null)o[k]={};o=o[k]});o[ks[ks.length-1]]=val}
function getPath(path){return path.split(".").reduce((o,k)=>o==null?o:o[k],C)}
function curWork(){return [...document.querySelectorAll("#workList button")].findIndex(b=>b.getAttribute("aria-current")==="true")}
function editable(el,path){
  if(!el||el.dataset.path===path)return;
  el.dataset.path=path;el.contentEditable="plaintext-only";el.spellcheck=false;el.classList.add("ed");
}
// texts inside buttons can't be typed into, so they get a box on double-click
function promptEdit(el,path){el.dataset.path=path;el.classList.add("ed","ed-dbl");el.title="ดับเบิลคลิกเพื่อแก้"}
// small buttons laid over a video or picture
function tools(host,key,btns){
  if(!host||host.querySelector(`:scope > .edt[data-key="${key}"]`))return;
  host.querySelectorAll(":scope > .edt").forEach(x=>x.remove());
  if(getComputedStyle(host).position==="static")host.style.position="relative";
  const d=document.createElement("div");d.className="edt";d.dataset.key=key;
  btns.forEach(([label,fn])=>{const b=document.createElement("button");b.type="button";b.textContent=label;
    b.onclick=e=>{e.preventDefault();e.stopPropagation();fn()};d.appendChild(b)});
  host.appendChild(d);
}
function addBtn(after,id,label,fn){
  if(!after||document.getElementById(id))return;
  const b=document.createElement("button");b.type="button";b.id=id;b.className="ed-add";b.textContent=label;b.onclick=fn;after.after(b);
}
function mark(){
  for(const id in IDS)editable(document.getElementById(id),IDS[id]);
  const k=curWork();
  if(k>=0){
    const i=document.getElementById("longInfo");editable(i.querySelector("h3"),`works.${k}.title`);editable(i.querySelector("p"),`works.${k}.desc`);
    const m=i.querySelector(".meta");if(m&&!m.classList.contains("ed")){m.classList.add("ed","ed-dbl");m.title="ดับเบิลคลิกเพื่อแก้ประเภทและปี";m.ondblclick=()=>editMeta(k)}
    const r=i.querySelector(".roles");if(r&&!r.classList.contains("ed")){r.classList.add("ed","ed-dbl");r.title="ดับเบิลคลิกเพื่อแก้หน้าที่";r.ondblclick=()=>editRoles(k)}
    const w=C.works[k];
    tools(document.querySelector(".pwrap"),"w"+k+(w.yt?"y":""),[["เปลี่ยนวิดีโอ",()=>media("work",k)],["เปลี่ยนภาพปก",()=>media("poster",k)],
      [w.yt?"YouTube ✓":"ใส่ลิงก์ YouTube",()=>editYt(k)],["ลบงานนี้",()=>remove("works",k,w.title)]]);
  }
  tools(document.querySelector("#s-home .stage"),"reel",[["เปลี่ยน Showreel",()=>media("showreel")],["ชื่อ Showreel",editReelTitle]]);
  document.querySelectorAll("#stillList figcaption").forEach((f,i)=>editable(f,`stills.${i}.title`));
  document.querySelectorAll("#stillList .frame").forEach((f,i)=>tools(f,"s"+i,[["เปลี่ยนรูป",()=>media("still",i)],["ลบ",()=>remove("stills",i)]]));
  document.querySelectorAll("#gfxList figcaption").forEach((f,i)=>editable(f,`graphics.${i}.title`));
  document.querySelectorAll("#gfxList .frame").forEach((f,i)=>tools(f,"g"+i,[["เปลี่ยน",()=>media("graphic",i)],["ลบ",()=>remove("graphics",i)]]));
  document.querySelectorAll("#shortList .sf > span:last-child").forEach((f,i)=>editable(f,`shorts.${i}.title`));
  document.querySelectorAll("#shortList .sfv").forEach((f,i)=>tools(f,"h"+i,[["เปลี่ยน",()=>media("short",i)],["ลิงก์",()=>editShortUrl(i)],["ลบ",()=>remove("shorts",i)]]));
  document.querySelectorAll("#tabs .l").forEach((l,i)=>promptEdit(l,"sections."+TABS[slides[i].id]));
  document.querySelectorAll("#workList .t").forEach((t,i)=>promptEdit(t,`works.${i}.tab`));
  document.querySelectorAll("#pLinks a").forEach((a,i)=>{if(!a.classList.contains("ed")){a.classList.add("ed","ed-dbl");a.title="คลิกเพื่อแก้ลิงก์";a.onclick=e=>{e.preventDefault();editLink(i)}}});
  addBtn(document.getElementById("workList"),"addWork","+ เพิ่มงาน Long-form",()=>media("addwork"));
  addBtn(document.getElementById("shortList"),"addShort","+ เพิ่มคลิปแนวตั้ง",()=>media("addshort"));
  addBtn(document.getElementById("stillList"),"addStill","+ เพิ่มภาพนิ่ง (รูป หรือเฟรมจากวิดีโอ)",()=>media("addstill"));
  addBtn(document.getElementById("gfxList"),"addGfx","+ เพิ่มกราฟิก / โมชั่น",()=>media("addgraphic"));
  addBtn(document.getElementById("pLinks"),"addLink","+ เพิ่มลิงก์",()=>editLink((C.profile.links=C.profile.links||[]).length));
}
function touched(){dirty=true;status("ยังไม่ได้บันทึก",true)}
function changed(el){const v=el.innerText.replace(/\s*\n\s*/g," ").trim();setPath(el.dataset.path,v);touched()}

// ---- prompts for things that aren't plain text on the page
function ask(q,v){const a=prompt(q,v??"");return a==null?null:a.trim()}
function editYt(k){
  const w=C.works[k],a=ask("วางลิงก์ YouTube ของคลิปเต็ม (ลบให้ว่าง = ไม่มีลิงก์)\nอัปแบบ ไม่เป็นสาธารณะ / Unlisted และเปิด \"อนุญาตให้ฝัง\"",w.yt?"https://youtu.be/"+w.yt:"");
  if(a==null)return;const id=ytId(a);if(a&&!id)return alert("ลิงก์นี้ไม่ใช่ลิงก์วิดีโอ YouTube");
  w.yt=id;touched();refresh();
}
function editMeta(k){
  const w=C.works[k],t=ask("ประเภท · ลูกค้า",w.type);if(t==null)return;const y=ask("ปี",w.year);if(y==null)return;
  w.type=t;w.year=/^\d+$/.test(y)?+y:y;touched();refresh();
}
function editRoles(k){const w=C.works[k],r=ask("หน้าที่ที่ทำ คั่นด้วยจุลภาค ,",(w.roles||[]).join(", "));if(r==null)return;w.roles=r.split(",").map(s=>s.trim()).filter(Boolean);touched();refresh()}
function editShortUrl(i){const s=C.shorts[i],u=ask("ลิงก์คลิปจริง (TikTok / Reels / Shorts) — ว่าง = ไม่มีลิงก์",s.url);if(u==null)return;s.url=u;const p=ask("แพลตฟอร์ม (ป้ายมุมขวาบน)",s.platform);if(p!=null)s.platform=p;touched();refresh()}
function editReelTitle(){const r=C.showreel,t=ask("ชื่อ Showreel (ขึ้นมุมซ้ายล่างของวิดีโอ)",r.title);if(t==null)return;r.title=t;touched();refresh()}
function editLink(i){
  const L=C.profile.links,l=L[i]||{label:"",url:""};
  const label=ask("ชื่อลิงก์ เช่น YouTube, Facebook, TikTok (ลบให้ว่าง = ลบลิงก์นี้)",l.label);if(label==null)return;
  if(!label){if(L[i]){L.splice(i,1);touched();refresh()}return}
  const url=ask("ที่อยู่ลิงก์ (https://...)",l.url);if(!url)return;
  L[i]={label,url:/^https?:\/\//.test(url)?url:"https://"+url};touched();refresh();
}
function remove(list,i,name){
  if(!confirm(`ลบ${name?` "${name}"`:"ชิ้นนี้"}ออกจากเว็บ?`))return;
  C[list].splice(i,1);if(list==="works")keepWork(0);touched();refresh();
}
// changes that alter lists or media are saved, then the page reloads to show them
async function refresh(){if(await save()){location.reload()}}
function keepWork(k){try{sessionStorage.setItem("edWork",k)}catch(e){}}

const HINT={time:d=>`วิดีโอยาว ${d}\nใช้วินาทีไหน? เช่น 0:12 หรือ 1:05:30 (เว้นว่าง = เลือกให้อัตโนมัติ)`,
  times:d=>`วิดีโอยาว ${d}\nนาทีที่อยากใช้เป็นไฮไลท์ คั่นด้วยจุลภาค เช่น 1:23, 5:40, 12:05\n(เว้นว่าง = เลือกช่วงเด่นให้อัตโนมัติ 6 ช่วง)`};
async function media(op,index){
  if(!await save())return;
  busy("เลือกไฟล์ในหน้าต่างที่เด้งขึ้นมา…");
  try{
    let r=await post("/media",{op,index});
    if(r.ask){
      const a=prompt(HINT[r.ask](r.dur),"");if(a==null){busy();return status("ยกเลิกแล้ว")}
      busy("กำลังประมวลผลวิดีโอ… คลิปยาวอาจใช้หลายนาที อย่าปิดหน้าต่างดำ");
      r=await post("/media",{op,index,file:r.file,[r.ask==="times"?"times":"t"]:a});
    }
    if(!r.ok){busy();return status(r.msg||"ทำไม่สำเร็จ",true)}
    keepWork(op==="addwork"?C.works.length:op==="work"||op==="poster"?index:curWork());
    location.reload();
  }catch(e){busy();status("ทำไม่สำเร็จ — หน้าต่างดำของ แก้เว็บ.bat ยังเปิดอยู่ไหม?",true)}
}

document.addEventListener("input",e=>{if(e.target.dataset&&e.target.dataset.path)changed(e.target)});
document.addEventListener("keydown",e=>{if(e.key==="Enter"&&e.target.isContentEditable){e.preventDefault();e.target.blur()}},true);
// don't follow links or start videos while editing a caption
document.addEventListener("click",e=>{if(e.target.isContentEditable)e.preventDefault()},true);
document.addEventListener("dblclick",e=>{
  const el=e.target.closest(".ed-dbl[data-path]");if(!el)return;e.preventDefault();
  const v=prompt("แก้ข้อความ",el.textContent);if(v==null||!v.trim())return;
  el.textContent=v.trim();changed(el);
});
new MutationObserver(mark).observe(document.body,{childList:true,subtree:true});

const css=document.createElement("style");
css.textContent=`.ed{outline:1px dashed color-mix(in srgb,currentColor 35%,transparent);outline-offset:3px;cursor:text;border-radius:2px}
.ed:hover,.ed:focus{outline:1px solid #3ea6ff}.ed-dbl{cursor:pointer}
.edt{position:absolute;left:8px;top:8px;z-index:6;display:flex;gap:6px;flex-wrap:wrap}
.edt button,.ed-add,#edBar button{font:500 13px/1.2 "Prompt",system-ui,sans-serif;border:1px solid #555;background:rgba(20,20,22,.88);color:#eee;border-radius:999px;padding:6px 12px;cursor:pointer}
.edt button:hover,.ed-add:hover{background:#3ea6ff;border-color:#3ea6ff;color:#fff}
.ed-add{display:block;width:fit-content;margin-top:12px;border-style:dashed;background:none;color:var(--fg)}
#edBar{position:fixed;left:50%;top:8px;transform:translateX(-50%);z-index:999;display:flex;gap:6px;align-items:center;padding:5px 6px 5px 14px;
 border-radius:999px;background:rgba(20,20,22,.94);color:#eee;font:13px/1.2 "Prompt",system-ui,sans-serif;box-shadow:0 4px 18px rgba(0,0,0,.35);white-space:nowrap}
#edBar button{background:none}#edBar button.go{background:#eee;color:#111;border-color:#eee}#edBar button:disabled{opacity:.4;cursor:default}
#edMsg{max-width:34vw;overflow:hidden;text-overflow:ellipsis}#edMsg.warn{color:#ffb547}
#edBusy{position:fixed;inset:0;z-index:1000;display:grid;place-items:center;background:rgba(0,0,0,.6);color:#fff;font:500 18px "Prompt",system-ui,sans-serif;text-align:center;padding:24px}`;
document.head.appendChild(css);
const bar=document.createElement("div");bar.id="edBar";
bar.innerHTML=`<b>โหมดแก้ไข</b><span id="edMsg" title="คลิกข้อความที่มีเส้นประเพื่อแก้"></span><button id="edPhoto" type="button">รูปโปรไฟล์</button><button id="edResume" type="button">รูป Resume</button><button id="edSave" type="button">บันทึก</button><button id="edPub" class="go" type="button">อัปขึ้นเว็บ</button>`;
document.body.appendChild(bar);
const msg=document.getElementById("edMsg");
function status(t,warn){msg.textContent=t;msg.title=t;msg.classList.toggle("warn",!!warn)}
function busy(t){let o=document.getElementById("edBusy");if(!t){o&&o.remove();return}if(!o){o=document.createElement("div");o.id="edBusy";document.body.appendChild(o)}o.textContent=t}
document.getElementById("edPhoto").onclick=()=>media("photo");
document.getElementById("edResume").onclick=()=>media("resume");

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

// back on the work that was being edited before the reload
try{const k=sessionStorage.getItem("edWork");sessionStorage.removeItem("edWork");if(k!=null&&C.works[+k])showWork(+k)}catch(e){}
mark();
})();
