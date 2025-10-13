// Vanilla JS Popup
//
// Usage:
//   import { Popup, PopupManager, popupConfirm, popupAlert } from "/static/js/ui/popup.js";
//   const p = new Popup("settings", { title: "Настройки", content: "Привет" }); p.open();

class PopupManager {
  static #instance;
  static get instance() {
    if (!PopupManager.#instance) PopupManager.#instance = new PopupManager();
    return PopupManager.#instance;
  }
  constructor() {
    this.stack = [];
    this.baseZ = 1000;
    this.lockedScrollCount = 0;
    this.#escHandler = this.#handleEsc.bind(this);
    this.#keydownAttached = false;
    this.#prevBodyOverflow = "";
    this.#ensureGlobalKeydown();
  }
  #escHandler; #keydownAttached; #prevBodyOverflow;

  #ensureGlobalKeydown() {
    if (!this.#keydownAttached) {
      document.addEventListener("keydown", this.#escHandler, true);
      this.#keydownAttached = true;
    }
  }
  register(popup){ if(!this.stack.find(p=>p.id===popup.id)) this.stack.push(popup); this.#reflowZ(); this.#updateBodyScrollLock(); }
  unregister(popup){ this.stack = this.stack.filter(p=>p!==popup); this.#reflowZ(); this.#updateBodyScrollLock(); }
  bringToFront(popup){ this.stack = this.stack.filter(p=>p!==popup); this.stack.push(popup); this.#reflowZ(); }
  anyModalOpen(){ return this.stack.some(p=>p.isOpen && p.options.modal); }
  getTop(){ return this.stack[this.stack.length-1]||null; }
  #reflowZ(){ let z=this.baseZ; for(const p of this.stack){ p._applyZ(z); z+=2; } }
  #updateBodyScrollLock(){ const lock=this.anyModalOpen(); if(lock && !this.lockedScrollCount){ this.#prevBodyOverflow=document.body.style.overflow; document.body.style.overflow="hidden"; this.lockedScrollCount=1; } else if(!lock && this.lockedScrollCount){ document.body.style.overflow=this.#prevBodyOverflow||""; this.lockedScrollCount=0; } }
  #handleEsc(e){ if(e.key!=="Escape")return; const top=this.getTop(); if(!top||!top.isOpen||!top.options.escClose)return; top._emit("esc",{originalEvent:e}); if(!e.defaultPrevented){ e.stopPropagation(); e.preventDefault(); top.close("esc"); } }
}

class Popup {
  constructor(id, options = {}) {
    if (!id || typeof id !== "string") throw new Error("Popup id (string) is required");
    this.id = id;
    this.options = Object.assign({
      modal: true,
      mount: document.body,
      escClose: true,
      backdropClose: true,
      closeButton: true,
      trapFocus: true,
      restoreFocus: true,
      role: "dialog",
      ariaLabel: null,
      ariaLabelledby: null,
      size: "md",
      maxWidth: "90vw",
      maxHeight: "90vh",
      position: "center",
      theme: "auto",
      animate: "fade",
      duration: 180,
      title: null,
      content: null,
      footer: null,
      sanitizeHTML: true,
      draggable: true,
      dragHandle: null,
      resizable: true,
      resizeEdges: ["right","bottom","corner"],
      keepInViewport: true,
      onBeforeOpen: null, onOpen: null, onBeforeClose: null, onClose: null,
      onEsc: null, onBackdrop: null,
      onDragStart: null, onDrag: null, onDragEnd: null,
      onResizeStart: null, onResize: null, onResizeEnd: null,
      debug: false
    }, options);

    this.isOpen = false;
    this._eventMap = new Map();
    this._savedFocus = null;
    this._animating = false;

    this.#buildDOM();
    this.#wireCoreEvents();
  }

  open(){
    if(this.isOpen||this._animating) return;
    if(this._emit("beforeopen")===false) return;
    this._savedFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;

    const { mount } = this.options;
    if(!mount || !(mount instanceof Element)) throw new Error("Invalid mount element");
    mount.appendChild(this._root);

    this.#applyTheme(); this.#applyRoleAndAria(); this.#applySizePosition(); this.#applyAnimation();

    PopupManager.instance.register(this);
    PopupManager.instance.bringToFront(this);

    if(this.options.modal && this._backdrop) this._backdrop.classList.add("popup-backdrop--visible");
    this._panel.classList.add("popup--open");
    this.isOpen = true;

    if(this.options.trapFocus){ setTimeout(()=>this.focusFirstElement(),0); this.#enableFocusTrap(); }

    if(typeof this.options.onBeforeOpen==="function") this.options.onBeforeOpen(this);
    setTimeout(()=>{ this._emit("open"); if(typeof this.options.onOpen==="function") this.options.onOpen(this); }, this.options.duration);
  }
  close(reason="programmatic"){
    if(!this.isOpen||this._animating) return;
    if(this._emit("beforeclose",{reason})===false) return;

    this.#applyAnimation();
    if(this.options.modal && this._backdrop) this._backdrop.classList.remove("popup-backdrop--visible");
    this._panel.classList.remove("popup--open");
    this.isOpen=false; this.#disableFocusTrap();

    setTimeout(()=>{ this._root.remove(); PopupManager.instance.unregister(this); this._emit("close",{reason});
      if(typeof this.options.onClose==="function") this.options.onClose(this,reason);
      if(this.options.restoreFocus && this._savedFocus && document.contains(this._savedFocus)){ try{ this._savedFocus.focus(); }catch{} }
    }, this.options.duration);
  }
  toggle(){ this.isOpen ? this.close("toggle") : this.open(); }
  destroy(){ this.close("destroy"); this.#teardownCoreEvents(); this._eventMap.clear(); }
  bringToFront(){ PopupManager.instance.bringToFront(this); }

  focusFirstElement(){ const list=this.#getFocusable(this._panel); if(list[0]) list[0].focus(); else this._panel.focus({preventScroll:true}); }
  shake(){ this._panel.classList.remove("popup--shake"); void this._panel.offsetWidth; this._panel.classList.add("popup--shake"); setTimeout(()=>this._panel.classList.remove("popup--shake"),400); }

  setTitle(v){ this.#setSlot(this._titleEl,v); }
  setContent(v){ this.#setSlot(this._bodyEl,v); }
  setFooter(v){ this.#setSlot(this._footerEl,v); }
  setLoading(on=true){ this._panel.classList.toggle("is-loading",!!on); if(on) this._errorRegion.textContent=""; }
  setError(msgOrNode){ this._panel.classList.add("is-error"); this.#setSlot(this._errorRegion,msgOrNode,true); }
  updateOptions(patch={}){ Object.assign(this.options,patch); this.#applyTheme(); this.#applyRoleAndAria(); this.#applySizePosition(); }

  attachForm(formEl, opts={}){
    if(!formEl) return;
    const { validate=null, onSubmit=null, submitSelector='button[type="submit"], [type="submit"]', disableWhileSubmit=true } = opts;
    const submitBtn = formEl.querySelector(submitSelector);

    const handler = async (e)=>{
      e.preventDefault(); this.setError("");
      let ok=true;
      if(typeof validate==="function"){ try{ ok=await validate(formEl); }catch(err){ ok=false; this.setError(err?.message||"Validation error"); this.shake(); } }
      if(!ok) return;
      try{
        if(disableWhileSubmit && submitBtn) submitBtn.disabled=true;
        this.setLoading(true);
        if(typeof onSubmit==="function"){ const res = await onSubmit(new FormData(formEl), formEl); this.close("submit"); return res; }
      }catch(err){ this.setError(err?.message||"Submit error"); this.shake(); }
      finally{ if(disableWhileSubmit && submitBtn) submitBtn.disabled=false; this.setLoading(false); }
    };
    formEl.addEventListener("submit", handler);
    return ()=>formEl.removeEventListener("submit", handler);
  }

  attachDragHandle(handleEl){ if(!(handleEl instanceof Element)) return; this._dragHandle=handleEl; this.#bindDrag(); }
  addEventListener(name,fn){ if(!this._eventMap.has(name)) this._eventMap.set(name,new Set()); this._eventMap.get(name).add(fn); }
  removeEventListener(name,fn){ this._eventMap.get(name)?.delete(fn); }

  // внутреннее
  _applyZ(base){ if(this._backdrop) this._backdrop.style.zIndex=String(base); this._panel.style.zIndex=String(base+1); }
  _emit(name, detail={}) {
    const cbName=({beforeopen:"onBeforeOpen",open:"onOpen",beforeclose:"onBeforeClose",close:"onClose",esc:"onEsc",backdrop:"onBackdrop",dragstart:"onDragStart",drag:"onDrag",dragend:"onDragEnd",resizestart:"onResizeStart",resize:"onResize",resizeend:"onResizeEnd"})[name];
    let prevented=false;
    const ev={ type:name, detail:Object.assign({popup:this},detail), preventDefault:()=>{prevented=true;}, get defaultPrevented(){return prevented;} };
    const set=this._eventMap.get(name); if(set) for(const fn of set){ try{ fn(ev); }catch(e){ if(this.options.debug) console.error(e); } }
    const cb=cbName&&this.options[cbName]; if(typeof cb==="function"){ try{ cb(this,ev); }catch(e){ if(this.options.debug) console.error(e); } }
    return prevented?false:true;
  }

  #buildDOM(){
    const root=document.createElement("div"); root.className="popup-root"; root.dataset.id=this.id;

    let backdrop=null;
    if(this.options.modal){ backdrop=document.createElement("div"); backdrop.className="popup-backdrop"; root.appendChild(backdrop); this._backdrop=backdrop; }

    const panel=document.createElement("div"); panel.className=`popup-obj popup--${this.#normalizeSize(this.options.size)}`; panel.tabIndex=-1; panel.setAttribute("data-popup-id",this.id); root.appendChild(panel);

    const header=document.createElement("div"); header.className="popup__header";
    const titleEl=document.createElement("h2"); titleEl.className="popup__title"; titleEl.id=`${this.id}-title`; header.appendChild(titleEl);

    let closeBtn=null;
    if(this.options.closeButton){ closeBtn=document.createElement("button"); closeBtn.className="popup__close"; closeBtn.type="button"; closeBtn.setAttribute("aria-label","Закрыть"); closeBtn.innerHTML="×"; header.appendChild(closeBtn); }

    const body=document.createElement("div"); body.className="popup__body";
    const errorRegion=document.createElement("div"); errorRegion.className="popup__error"; errorRegion.setAttribute("aria-live","polite");
    const footer=document.createElement("div"); footer.className="popup__footer";

    panel.appendChild(header); panel.appendChild(body); panel.appendChild(errorRegion); panel.appendChild(footer);

    if(this.options.resizable){
      const edges=new Set(this.options.resizeEdges);
      if(edges.has("right")){ const h=document.createElement("div"); h.className="popup__resize-handle popup__resize--right"; panel.appendChild(h); }
      if(edges.has("bottom")){ const h=document.createElement("div"); h.className="popup__resize-handle popup__resize--bottom"; panel.appendChild(h); }
      if(edges.has("corner")){ const h=document.createElement("div"); h.className="popup__resize-handle popup__resize--corner"; panel.appendChild(h); }
    }

    this._root=root; this._panel=panel; this._headerEl=header; this._titleEl=titleEl; this._bodyEl=body; this._footerEl=footer; this._closeBtn=closeBtn; this._errorRegion=errorRegion;
    this.setTitle(this.options.title); this.setContent(this.options.content); this.setFooter(this.options.footer);
  }

  #wireCoreEvents(){
    this._onBackdropClick=(e)=>{ if(!this.options.backdropClose) return; if(e.target===this._backdrop){ const prevented=this._emit("backdrop",{originalEvent:e})===false; if(!prevented) this.close("backdrop"); } };
    if(this._backdrop) this._backdrop.addEventListener("click",this._onBackdropClick);

    this._onCloseClick=()=>this.close("button");
    if(this._closeBtn) this._closeBtn.addEventListener("click",this._onCloseClick);

    if(this.options.draggable){ this._dragHandle=this.options.dragHandle ? (typeof this.options.dragHandle==="string" ? this._panel.querySelector(this.options.dragHandle) : this.options.dragHandle) : this._headerEl; this.#bindDrag(); }
    if(this.options.resizable) this.#bindResizeHandles();
  }

  #teardownCoreEvents(){
    if(this._backdrop&&this._onBackdropClick) this._backdrop.removeEventListener("click",this._onBackdropClick);
    if(this._closeBtn&&this._onCloseClick) this._closeBtn.removeEventListener("click",this._onCloseClick);
    this.#unbindDrag(); this.#unbindResize(); this.#disableFocusTrap();
  }

  #bindDrag(){
    this.#unbindDrag(); if(!this._dragHandle) return;
    this._dragStart=(e)=>{ const pe=e.touches?e.touches[0]:e; this._dragging=true; this._panel.classList.add("is-dragging"); const rect=this._panel.getBoundingClientRect(); this._dragOffsetX=pe.clientX-rect.left; this._dragOffsetY=pe.clientY-rect.top; this._panel.style.willChange="transform"; this._emit("dragstart",{x:rect.left,y:rect.top});
      document.addEventListener("mousemove",this._dragMove); document.addEventListener("touchmove",this._dragMove,{passive:false}); document.addEventListener("mouseup",this._dragEnd); document.addEventListener("touchend",this._dragEnd); e.preventDefault(); };
    this._dragMove=(e)=>{ if(!this._dragging) return; const pe=e.touches?e.touches[0]:e; let x=pe.clientX-this._dragOffsetX; let y=pe.clientY-this._dragOffsetY;
      if(this.options.keepInViewport){ const vw=document.documentElement.clientWidth; const vh=document.documentElement.clientHeight; const rect=this._panel.getBoundingClientRect(); const w=rect.width; const h=rect.height; x=Math.max(0,Math.min(x,vw-w)); y=Math.max(0,Math.min(y,vh-h)); }
      this._panel.style.left=`${x}px`; this._panel.style.top=`${y}px`; this._panel.style.transform="none"; this._panel.style.position="fixed"; this._emit("drag",{x,y}); if(e.cancelable) e.preventDefault(); };
    this._dragEnd=()=>{ if(!this._dragging) return; this._dragging=false; this._panel.classList.remove("is-dragging"); this._panel.style.willChange=""; this._emit("dragend");
      document.removeEventListener("mousemove",this._dragMove); document.removeEventListener("touchmove",this._dragMove); document.removeEventListener("mouseup",this._dragEnd); document.removeEventListener("touchend",this._dragEnd); };
    this._dragHandle.addEventListener("mousedown",this._dragStart); this._dragHandle.addEventListener("touchstart",this._dragStart,{passive:false}); this._dragBound=true; this._panel.classList.add("is-draggable");
  }
  #unbindDrag(){ if(!this._dragBound||!this._dragHandle) return; this._dragHandle.removeEventListener("mousedown",this._dragStart); this._dragHandle.removeEventListener("touchstart",this._dragStart); this._dragBound=false; this._panel.classList.remove("is-draggable"); }

  #bindResizeHandles(){
    this._resizeHandlers=[]; const handles=this._panel.querySelectorAll(".popup__resize-handle");
    handles.forEach(h=>{
      const type = h.classList.contains("popup__resize--corner") ? "corner" : (h.classList.contains("popup__resize--right") ? "right" : "bottom");
      const start=(e)=>{ const pe=e.touches?e.touches[0]:e; this._resizing=type; const rect=this._panel.getBoundingClientRect();
        this._resizeStartRect={x:rect.left,y:rect.top,w:rect.width,h:rect.height}; this._resizeStartPoint={x:pe.clientX,y:pe.clientY};
        this._panel.classList.add("is-resizing"); this._emit("resizestart",{type,rect});
        document.addEventListener("mousemove",move); document.addEventListener("touchmove",move,{passive:false}); document.addEventListener("mouseup",end); document.addEventListener("touchend",end); e.preventDefault(); };
      const move=(e)=>{ if(!this._resizing) return; const pe=e.touches?e.touches[0]:e; const dx=pe.clientX-this._resizeStartPoint.x; const dy=pe.clientY-this._resizeStartPoint.y;
        let w=this._resizeStartRect.w, h=this._resizeStartRect.h;
        if(this._resizing==="right"||this._resizing==="corner") w=Math.max(240,this._resizeStartRect.w+dx);
        if(this._resizing==="bottom"||this._resizing==="corner") h=Math.max(160,this._resizeStartRect.h+dy);
        this._panel.style.width=`${w}px`; this._panel.style.height=`${h}px`; this._emit("resize",{type:this._resizing,width:w,height:h}); if(e.cancelable) e.preventDefault(); };
      const end=()=>{ if(!this._resizing) return; this._panel.classList.remove("is-resizing"); this._emit("resizeend",{type:this._resizing}); this._resizing=null;
        document.removeEventListener("mousemove",move); document.removeEventListener("touchmove",move); document.removeEventListener("mouseup",end); document.removeEventListener("touchend",end); };
      h.addEventListener("mousedown",start); h.addEventListener("touchstart",start,{passive:false}); this._resizeHandlers.push({h,start});
    });
    this._panel.classList.add("is-resizable");
  }
  #unbindResize(){ if(!this._resizeHandlers) return; this._resizeHandlers.forEach(({h,start})=>{ h.removeEventListener("mousedown",start); h.removeEventListener("touchstart",start); }); this._resizeHandlers=null; this._panel.classList.remove("is-resizable"); }

  #getFocusable(root){
    return Array.from(root.querySelectorAll([
      "a[href]","button:not([disabled])","textarea:not([disabled])","input:not([disabled])","select:not([disabled])","[tabindex]:not([tabindex='-1'])"
    ].join(","))).filter(el=>el.offsetParent!==null || el===document.activeElement);
  }
  #enableFocusTrap(){
    this._focusTrap=(e)=>{ if(!this.isOpen||!this.options.trapFocus) return; if(e.key!=="Tab") return;
      const list=this.#getFocusable(this._panel); if(list.length===0){ e.preventDefault(); this._panel.focus(); return; }
      const first=list[0], last=list[list.length-1];
      if(e.shiftKey && document.activeElement===first){ e.preventDefault(); last.focus(); }
      else if(!e.shiftKey && document.activeElement===last){ e.preventDefault(); first.focus(); }
    };
    document.addEventListener("keydown",this._focusTrap,true);
  }
  #disableFocusTrap(){ if(this._focusTrap){ document.removeEventListener("keydown",this._focusTrap,true); this._focusTrap=null; } }

  #setSlot(target, value, forceText=false){
    if(!target) return;
    while(target.firstChild) target.removeChild(target.firstChild);
    if(value==null) return;
    if(typeof value==="function") return this.#setSlot(target,value(),forceText);
    if(value instanceof Node) return void target.appendChild(value);
    if(typeof value==="string"){ if(this.options.sanitizeHTML||forceText) target.textContent=value; else target.innerHTML=value; return; }
    target.textContent=String(value);
  }

  #applyTheme(){ const t=this.options.theme; this._panel.removeAttribute("data-theme"); if(t==="light"||t==="dark") this._panel.setAttribute("data-theme",t); }
  #applyRoleAndAria(){
    const role=this.options.role==="alertdialog"?"alertdialog":"dialog";
    this._panel.setAttribute("role",role); this._panel.setAttribute("aria-modal",String(!!this.options.modal));
    if(this.options.ariaLabelledby) this._panel.setAttribute("aria-labelledby",this.options.ariaLabelledby);
    else if(this._titleEl?.id) this._panel.setAttribute("aria-labelledby",this._titleEl.id);
    if(this.options.ariaLabel) this._panel.setAttribute("aria-label",this.options.ariaLabel);
  }
  #normalizeSize(s){ return typeof s==="string" ? s : "custom"; }
  #applySizePosition(){
    const { size,maxWidth,maxHeight,position }=this.options;
    this._panel.style.maxWidth=typeof maxWidth==="number"?`${maxWidth}px`:maxWidth;
    this._panel.style.maxHeight=typeof maxHeight==="number"?`${maxHeight}px`:maxHeight;

    if(typeof size==="object"&&size){ if(size.width) this._panel.style.width=typeof size.width==="number"?`${size.width}px`:size.width; if(size.height) this._panel.style.height=typeof size.height==="number"?`${size.height}px`:size.height; }
    else { this._panel.style.width=""; this._panel.style.height=""; }

    this._panel.style.left=""; this._panel.style.top=""; this._panel.style.right=""; this._panel.style.position=""; this._panel.style.transform="";

    if(position==="center"){ this._panel.classList.add("popup--center"); }
    else{
      this._panel.classList.remove("popup--center");
      const coords = typeof position==="object" ? position : (position==="top-right" ? { right:24, y:24 } : null);
      if(coords){ this._panel.style.position="fixed";
        if(coords.right!=null) this._panel.style.right=typeof coords.right==="number"?`${coords.right}px`:coords.right;
        if(coords.x!=null) this._panel.style.left=typeof coords.x==="number"?`${coords.x}px`:coords.x;
        if(coords.y!=null) this._panel.style.top=typeof coords.y==="number"?`${coords.y}px`:coords.y;
      } else { this._panel.classList.add("popup--center"); }
    }
  }
  #applyAnimation(){ this._animating=true; this._panel.style.setProperty("--popup-anim-ms", `${this.options.duration}ms`); if(this._backdrop) this._backdrop.style.setProperty("--popup-anim-ms", `${this.options.duration}ms`); setTimeout(()=>{ this._animating=false; }, this.options.duration); }
}

/* Presets */
function popupConfirm({ title="Подтверждение", message="", confirmText="OK", cancelText="Отмена", ...opts } = {}){
  return new Promise((resolve)=>{
    const content=document.createElement("div");
    const msg=document.createElement("div"); msg.className="popup__confirm-message"; msg.textContent=message;
    const actions=document.createElement("div"); actions.className="popup__actions";
    const ok=document.createElement("button"); ok.type="button"; ok.textContent=confirmText; ok.className="popup__btn popup__btn--primary";
    const cancel=document.createElement("button"); cancel.type="button"; cancel.textContent=cancelText; cancel.className="popup__btn";
    actions.append(ok,cancel); content.append(msg,actions);
    const p=new Popup(`confirm-${Date.now()}`, { title, content, ...opts, onClose: (_pp, reason)=>resolve(reason==="confirmed") });
    ok.addEventListener("click",()=>p.close("confirmed")); cancel.addEventListener("click",()=>p.close("cancel")); p.open();
  });
}
function popupAlert({ title="Сообщение", message="", okText="OK", role="alertdialog", ...opts } = {}){
  return new Promise((resolve)=>{
    const content=document.createElement("div");
    const msg=document.createElement("div"); msg.className="popup__confirm-message"; msg.textContent=message;
    const actions=document.createElement("div"); actions.className="popup__actions";
    const ok=document.createElement("button"); ok.type="button"; ok.textContent=okText; ok.className="popup__btn popup__btn--primary";
    actions.append(ok); content.append(msg,actions);
    const p=new Popup(`alert-${Date.now()}`, { title, content, role, ...opts, onClose: ()=>resolve() });
    ok.addEventListener("click",()=>p.close("ok")); p.open();
  });
}

export { Popup, PopupManager, popupConfirm, popupAlert };