// SHORTCUTS
let log = console.log;
let bdy = document.body;
let dir = console.dir;
let html = document.documentElement;
let getCoords = function(elem, true_form){
    let box = elem.getBoundingClientRect();

    if (true_form) return box;
    return{
        height: box.height,
        width: box.width,
        top: box.top + html.scrollTop,
        bottom: box.bottom + html.scrollTop,
        left: box.left + html.scrollLeft,
        right: box.right + html.scrollLeft
    }
}
let find = (str, elem) => {
    if (elem) return elem?.querySelector(str);
    else return document.querySelector(str);
};
let finds = (str, elem) => {
    if (elem) return Array.from(elem?.querySelectorAll(str));
    else return Array.from(document.querySelectorAll(str));
};
let list_ = Array.from;
let results;
function selectWithKeyboard(e){
    if (e.key == 'Enter') e.currentTarget.click();
}
let pageURL = new URL(window.location);
let sidebar = find('.sidebar');
let modalObj, dropdownObj, tabObj, floatObj, tab2Obj, customDetailsObj;
let dropdownObjs = [];
let tab2Objs = [];
let modalObjs = [];
let modalBtns = [];
let tab2Elems = [];
let copyBtns = [];
let customDetailsElems = [];
let changeIconTimeout, formerIconName;

let loadingTimeout;
let loadingCancelled;


// PREVENT FLASH ON FAST LOADS
document.body.addEventListener('htmx:configRequest', function(e) {
    let indicatorElem = find( e.target.getAttribute('hx-indicator') )
    loadingCancelled = false
    
    loadingTimeout = setTimeout(() => {
        if (loadingCancelled) return;
        if (indicatorElem) indicatorElem.style.display = 'block'
    }, 400); 

    finds('[hx-disable-submit]').forEach((btn) => {
        btn.disabled = true;
    })
});
document.body.addEventListener('htmx:afterRequest', function(e) {
    let indicatorElem = find( e.target.getAttribute('hx-indicator') );
    loadingCancelled = true;
    clearTimeout(loadingTimeout);
    if (indicatorElem) indicatorElem.style.display = 'none';

    if (!e.target.closest('.float_container')) {
        initCustomDetails();
        initTabs2();
        initCopyLogic();
        finds('[hx-clear-input]').forEach((inp) => {
            inp.value = '';
        })

        finds('[hx-disable-submit]').forEach((btn) => {
            btn.disabled = false;
        })
    }
});


// ALL BUTTONS AND BUTTON LIKE ELEMENTS CAN BE CLICKED WITH KEYBOARD
finds('[data-button]').forEach((btn) => {
    btn.addEventListener('keydown', selectWithKeyboard)
})

// HIGHLIGHT DIV WHEN INPUT RECEIVES FOCUS
bdy.addEventListener('focusin', (e) => {
    if (e.target.classList.contains('form_input')) {
        e.target.closest('.input_field').classList.add('form_input_active')
    }
})
bdy.addEventListener('focusout', (e) => {
    if (e.target.classList.contains('form_input')) {
        e.target.closest('.input_field').classList.remove('form_input_active')
    }
})

// HIDING AND SHOWING OF PASSWORD.   
let hideParams = {
    hide: { type: 'text', clsName: 'ri-eye-line', state: 'show' },
    show: {type: 'password', clsName: 'ri-eye-close-line', state: 'hide'}
}
let hideBtns = finds('.hide_btn');
hideBtns.forEach((hideBtn) => {
    hideBtn.addEventListener('click', (e) => {
        e.preventDefault();
        let param = hideParams[hideBtn.dataset.state]
        let input = hideBtn.previousElementSibling;
        input.setAttribute('type', param['type']);
        hideBtn.firstElementChild.className = param['clsName'];
        hideBtn.dataset.state = param['state']
    })
})

// ENSURING NEW AND CONFIRM PASSWORDS BOTH MATCH. change_password.html
let pwdInput = find('.pwd_input');
let pwdInput2 = find('.pwd_input2');
let submitBtn = find('input[type = "submit"')

function matchPwds(){
    let errContainer = find('.form_error_txt small');
    if (pwdInput2.value !== '' && (pwdInput.value !== pwdInput2.value)) {
        let errTxt = 'Passwords do not match';
        errContainer.textContent = errTxt;
        submitBtn.disabled = true;
    } else {
        errContainer.textContent = '';
        submitBtn.disabled = false
    }
}

// TOGGLE SIDEBAR ON MOBILE
function toggleSidebar(){
    let sidebarOverlay = find('.sidebar_overlay');
    sidebar.classList.toggle('show');
    sidebarOverlay.classList.toggle('show')

    if (sidebar.classList.contains('show')) bdy.style.overflow = 'hidden';
    else bdy.style.overflow = 'auto';
}

// FILL IN ICONS ON HOVER
function fillInIcon(iconBtn){
    if (iconBtn) {
        let iElem = find('i', iconBtn);
        if (!iElem) return;
        iElem.className = iElem.className.slice(0, -5) + '-fill';
    }
}
function toggleIconFill(iconBtn){
    let iElem = find('i', iconBtn);
    if (!iElem) return;
    iconBtn.addEventListener('pointerover', (e) => {
        if (!iconBtn.classList.contains('active_item')){
            iElem.className = iElem.className.slice(0, -5) + '-fill';
        }
    })
    
    iconBtn.addEventListener('pointerout', (e) => {
        if (!iconBtn.classList.contains('active_item')){
            iElem.className = iElem.className.slice(0, -5) + '-line';
        }
    })
}
finds('[data-icon-fill]').forEach((iconBtn) => { toggleIconFill(iconBtn) });
fillInIcon( find('.sidebar_nav .active_item'));




// CHANGING ICON AFTER TOGGLING DETAILS
function changeDetailIcon(e){
    let iElem = find('span i', e.currentTarget);
    if (iElem === null) return;
    if (iElem.className.startsWith('ri-arrow') && iElem.className.endsWith('s-line')) {
        if (iElem.className.includes('-up-') ){
            iElem.className = iElem.className.replace('up', 'down');
        } else {
            iElem.className = iElem.className.replace('down', 'up');
        }
    }
}
finds('summary').forEach((sum) => {
    sum.addEventListener('click', changeDetailIcon );
})



// RENDERING VARIABLE IMAGES FROM DJANGO
finds('[data-bg]').forEach((elem) => {
    let imgPath = elem.dataset.bg;
    elem.style.backgroundImage = `url("${imgPath}")`;
})



// FINDING LEFTOVER SPACE
function findAvailablePageHeight(elem){
    let cds = getCoords(elem);
    let computedStyles = getComputedStyle(elem);
    return `calc(100vh - ${cds.top}px - ${computedStyles.paddingBottom})`;
}

function resizeGdSections(){
    let gdSections = find('.gd_sections');
    if (gdSections){
        gdSections.style.setProperty('--left-over-height', findAvailablePageHeight(gdSections));
    }
}

resizeGdSections();






class ModalObj{
    constructor(btn){
        this.btn = btn;
        let modalId = btn.dataset.modal;
        this.modalContainer = document.getElementById(modalId);

        this.overlay = document.createElement('div');
        this.overlay.classList.add('overlay');
        this.overlay.addEventListener('click', this.closeModal.bind(this));
        this.showModalEvt = new CustomEvent('showModal', {bubbles: true, cancelable: true, detail: {modal_container: this.modalContainer, modal_btn: this.btn}});
        this.hideModalEvt = new CustomEvent('hideModal', {bubbles: true, cancelable: true, detail: {modal_container: this.modalContainer, modal_btn: this.btn}});
        
        // ADDING THE LISTENERS
        btn.addEventListener('click', this.openModal.bind(this))
        finds('.md_close', this.modalContainer).forEach((closeBtn) => {
            closeBtn.addEventListener('click', this.closeModal.bind(this));
        })
        this.modalContainer?.addEventListener('hx_close_modal', this.closeModal.bind(this));
    }
    
    boundFocusHandler = this.trapFocus.bind(this);
    boundKeyupHandler = this.keyupHandler.bind(this);

    openModal(){
        let modalContainer = this.modalContainer;
        if (this.checkForOpenModals() === true) this.deleteAllOpenModals();

        modalContainer.classList.add('open');
        this.btn.dispatchEvent(this.showModalEvt);
        this.modalContainer.prepend(this.overlay);
        
        this.btn.ariaExpanded = true;
        bdy.addEventListener('focusin', this.boundFocusHandler)
        bdy.addEventListener('focusout', this.boundFocusHandler)
        bdy.addEventListener('keyup', this.boundKeyupHandler);
        bdy.style.overflow = 'hidden';
    }

    closeModal(){
        this.modalContainer.classList.remove('open');
        this.overlay.remove();
        bdy.removeEventListener('focusin', this.boundFocusHandler);
        bdy.removeEventListener('focusout', this.boundFocusHandler);
        bdy.removeEventListener('keyup', this.boundKeyupHandler);
        bdy.style.overflow = 'auto';
        this.btn.focus();
        this.btn.ariaExpanded = false;
        this.btn.dispatchEvent(this.hideModalEvt);
    }

    checkForOpenModals(){
        let openedModals = finds('.modalContainer.open');
        return openedModals.length > 0;
    }
    deleteAllOpenModals(){
        let openedModals = finds('.modalContainer.open');
        openedModals.forEach((openedModal) => {
            openedModal.classList.remove('open');
            bdy.removeEventListener('focusin', this.boundFocusHandler);
            bdy.removeEventListener('focusout', this.boundFocusHandler);
        })
    }

    trapFocus(e){
        if (!e.target.closest(`#${this.modalContainer.id}`)) {
            find('button', this.modalContainer).focus();
        }
    }
    keyupHandler(e){
        if (e.key == 'Escape') this.closeModal();
    }
}
function initModals(){
    finds('[data-modal]').forEach((btn) => {
        modalObj = new ModalObj(btn);
        modalObjs.push(modalObj);
        modalBtns.push(modalObj.btn);
    })
}
initModals()


class DropdownObj{
    constructor(btn){
        this.dropdownDiv = document.getElementById(btn.dataset.dropdown);
        this.btnHeight = btn.getBoundingClientRect().height;
        this.btn = btn;
        this.ddContainer = this.dropdownDiv.closest('.dropdown_container');
        this.containerProps = this.ddContainer.getBoundingClientRect();
        this.dropdownAlignment = btn.dataset.dropdownAlign || 'none';

        btn.addEventListener('click', this.toggleDropdown.bind(this));
    }
    toggleDropdown(e){
        this.dropdownDiv.classList.toggle('show');
        this.hideOtherOpenDropdowns()
        if (this.dropdownDiv.classList.contains('show')) {
            this.positionDropdown()
        } 
        e.preventDefault();
    }
    positionDropdown(){
        if (this.spaceForDropdown()) {
            this.dropdownDiv.style.top = this.containerProps.height + 'px';
            this.dropdownDiv.style.bottom = '';
        } else {
            this.dropdownDiv.style.bottom = this.btnHeight + 'px';
            this.dropdownDiv.style.top = '';
        }

        if (this.spaceForDropdownX() && this.dropdownAlignment !== 'left'){
            this.dropdownDiv.style.left = 0;
        } else{
            let currentContainerProps = getCoords(this.ddContainer);
            let dropdownProperties = getCoords(this.dropdownDiv);
            this.dropdownDiv.style.left = ( currentContainerProps.width - dropdownProperties.width) + 'px';
        }
    }
    hideOtherOpenDropdowns(){
        let otherOpen = finds('.dropdown.show').filter((dd) => {
            return dd != this.dropdownDiv;
        })
        otherOpen.forEach((dd) => dd.classList.remove('show'))
    }
    spaceForDropdown(){
        let btnProperties = getCoords(this.btn, true);
        let dropdownProperties = getCoords(this.dropdownDiv);
        return (window.innerHeight - btnProperties.bottom) > (5 + dropdownProperties.height);
    }
    spaceForDropdownX(){
        let currentContainerProps = getCoords(this.ddContainer);

        let spaceLeftX = window.innerWidth - currentContainerProps.left;
        let dropdownProperties = getCoords(this.dropdownDiv);
        return spaceLeftX > (dropdownProperties.width + 5);
    }
}


function hideDropdown(e){
    if (!e.target.closest('[data-dropdown]') && !e.target.closest('.dropdown')) {
        finds('.dropdown').forEach((dd) => {
            dd.classList.remove('show');
        })
    }
}

bdy.addEventListener('click', hideDropdown);
window.addEventListener('resize', (e) => {
    resizeGdSections();

    let dd = find('.dropdown.show');
    if (dd == null) return;

    let ddObj = dropdownObjs.find((obj_) => {
        return obj_.dropdownDiv === dd;
    })
    if (ddObj == null) return;

    ddObj.positionDropdown();
})





class Tab2Obj{
    constructor(btn){
        this.sameTabBtns = finds(`[data-tab2 = ${btn.dataset.tab2}]`);
        this.tabElem = document.getElementById(btn.dataset.tab2);
        this.tabsHolder = this.tabElem.parentElement;
        btn.addEventListener('click', this.showTab.bind(this));
        this.tabName = this.tabElem.dataset.tabName || this.tabElem.id;
    }
    showTab(e){
        if (this.tabElem.classList.contains('active_tab2')) return;

        if (!this.tabsHolder.closest('[role = tabpanel]')){
            pageURL.searchParams.set('tab', this.tabName);
            history.pushState({}, '', pageURL);
        }

        list_(this.tabsHolder.children).forEach((tab) => {
            tab.classList.remove('active_tab2');
            
            let tabBtns = finds(`[data-tab2 = ${tab.id}]`);
            tabBtns.forEach((tabBtn) => {
                tabBtn.classList.remove('active_tab_btn2');
                tabBtn.ariaSelected = false;
                tabBtn.setAttribute('tabindex', '-1');
            })
        });
        this.tabElem.style.display = '';
        this.tabElem.classList.add('active_tab2');
        this.sameTabBtns.forEach((btn) => {
            btn.classList.add('active_tab_btn2');
            btn.ariaSelected = true;
            btn.setAttribute('tabindex', '0');
        })
    }
}

function initTabs2(){
    finds('[data-tab2]').forEach((btn) => {
        tab2Obj = new Tab2Obj(btn);

        if (!tab2Elems.includes(tab2Obj.tabElem)){
            tab2Elems.push(tab2Obj.tabElem);
            tab2Objs.push(tab2Obj);
        } 
    })
}
initTabs2()

function showPathTab(pathIds, defaultTab){
    let params = new URLSearchParams(window.location.search);
    let tabStr = params.get('tab') || defaultTab;
    let pathId = pathIds[tabStr];
    if (!pathId) return;

    let pathTab = document.getElementById(pathId);
    tab2Objs.forEach((obj_) => {
        if (obj_.tabElem == pathTab){ 
            obj_.showTab()
            return;
        }
    })
}





class FloatObj{
    constructor(floatElem){
        this.floatElem = floatElem;
        let closeBtn = document.createElement('button');
        closeBtn.classList.add('icon_btn');
        closeBtn.innerHTML = '<i class="ri-close-large-line"></i>';
        closeBtn.addEventListener('click', this.hideFloat.bind(this));
        floatElem.append(closeBtn);
        
        let floatRemoveTimeout;
        this.floatRemoveTimeout = floatRemoveTimeout;
        this.showFloatEvent = new CustomEvent('showFloat', {bubbles: true, cancelable: true, detail: {float_elem: floatElem }});
        bdy.addEventListener('keyup', this.hideFloatWithEscape.bind(this));

        this.showFloat()
    }
    showFloat(){
        clearTimeout(this.floatRemoveTimeout);
        this.floatElem.classList.add('show_float');
        bdy.dispatchEvent(this.showFloatEvent);

        this.floatRemoveTimeout = setTimeout(() => {
            this.hideFloat('slow');
        }, 5000)
    }
    hideFloat(){
        this.floatElem.classList.remove('show_float');
        clearTimeout(this.floatRemoveTimeout);
    }
    hideFloatWithEscape(e){
        if (e.key == 'Escape') this.hideFloat();
    }
}
function initFloats(){
    finds('[data-float]').forEach((float) => {
        floatObj = new FloatObj(float);
    })
}
initFloats()
bdy.addEventListener('hx_message', initFloats)



class CustomDetailsObj{
    constructor(elem){
        this.toggleBtn = document.getElementById( elem.dataset.detailToggle );
        this.detailsElem = elem;
        this.toggleBtn.addEventListener('click', this.toggleDetailsOpen.bind(this));
        this.showDetailsEvt = new CustomEvent('showDetails', {bubbles: true, cancelable: true, detail: {details_elem: this.detailsElem, details_btn: this.toggleBtn}});
        this.hideDetailsEvt = new CustomEvent('hideDetails', {bubbles: true, cancelable: true, detail: {details_elem: this.detailsElem, details_btn: this.toggleBtn}});
    }
    toggleDetailsOpen(e){
        if (!e.target.closest('.detail_dead_zone')){
            this.detailsElem.classList.toggle('open');
        }
        if (this.detailsElem.classList.contains('open')){
            this.toggleBtn.dispatchEvent(this.showDetailsEvt);
        } else{
            this.toggleBtn.dispatchEvent(this.hideDetailsEvt);
        }
    }
}
function initCustomDetails(){
    finds('[data-detail-toggle]').forEach((elem) => {
        if (!customDetailsElems.includes(elem)){
            customDetailsObj = new CustomDetailsObj(elem);
            customDetailsElems.push(elem);
        }
    })
}
initCustomDetails()




class copyLogic{
    constructor(btn){
        let copied = btn.dataset.copied;
        let changeIconTimeout, formerIconName, formerSvgElem;
        this.elemCopied = document.getElementById(copied);
        this.iElem = find('i', btn);
        this.changeIconTimeout = changeIconTimeout;
        this.formerIconName = formerIconName;
        this.btn = btn;
        this.formerSvgElem = formerSvgElem;
        this.svgElem = btn.firstElementChild;
        this.svgPath = find('path', this.svgElem);
        this.svgRect = find('rect', this.svgElem);

        btn.addEventListener('click', this.copyText.bind(this));
        if (btn.firstElementChild instanceof SVGElement){
            btn.addEventListener('click', this.changeSvgForSeconds.bind(this));
        } else {
            btn.addEventListener('click', this.changeIconForSeconds.bind(this));
        }
    }
    copyText(e){
        let copiedTxt = this.elemCopied.textContent || this.elemCopied.value;
        navigator.clipboard.writeText(copiedTxt.trim());
    }
    changeIconForSeconds(e){
        if (this.changeIconTimeout) {
            clearTimeout(this.changeIconTimeout);
        } else {
            this.formerIconName = this.iElem.className;
        }

        this.iElem.className = 'ri-check-line';
        this.changeIconTimeout = setTimeout(() => {
            if (this.formerIconName) this.iElem.className = this.formerIconName;
        }, 3000)
    }
    changeSvgForSeconds(e){
        if (this.changeIconTimeout) {
            clearTimeout(this.changeIconTimeout);
        } else{
            this.formerSvgPath = find('path', this.svgElem);
        }
        
        this.svgElem.innerHTML = "<path d = 'M5 13l4 4L19 7'>";
        this.changeIconTimeout = setTimeout(() => {
            if (this.formerSvgPath) {
                this.svgElem.innerHTML = '';
                this.svgElem.append(this.svgRect, this.svgPath);
            }
        }, 3000)
    }
}

function initCopyLogic(){
    finds('[data-copied]').forEach((c_btn) => {
        if (!copyBtns.includes(c_btn)) {
            copyObj = new copyLogic(c_btn);
            copyBtns.push(c_btn);
        }
    })
}
initCopyLogic()




document.addEventListener('DOMContentLoaded', () => {
    finds('[data-dropdown]').forEach((btn) => {
        dropdownObj = new DropdownObj(btn);
        dropdownObjs.push(dropdownObj);
    })
})


