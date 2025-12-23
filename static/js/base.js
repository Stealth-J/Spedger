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
let sidebar = find('.sidebar');
let modalObj, dropdownObj, tabObj, floatObj, tab2Obj;
let dropdownObjs = [];
let changeIconTimeout, formerIconName;



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
        iElem.className = iElem.className.slice(0, -5) + '-fill';
    }
}
function toggleIconFill(iconBtn){
    let iElem = find('i', iconBtn);
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

// COPYING TEXT AND UPDATING ICON AFTER COPYING
function copyText(e){
    let copied = e.currentTarget.dataset.copied;
    let elemCopied = document.getElementById(copied);
    let copiedTxt = elemCopied.textContent || elemCopied.value;
    navigator.clipboard.writeText(copiedTxt.trim());
}
function changeIconForSeconds(e){
    let iElem = find('i', e.currentTarget);
    if (changeIconTimeout) {
        clearTimeout(changeIconTimeout);
    } else {
        formerIconName = iElem.className;
    }
    
    find('i', e.currentTarget).className = 'ri-check-line';
    
    changeIconTimeout = setTimeout(() => {
        if (formerIconName) iElem.className = formerIconName;
    }, 3000);
}
finds('[data-copied]').forEach((c_btn) => {
    c_btn.addEventListener('click', copyText);
    c_btn.addEventListener('click', changeIconForSeconds);
})

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

finds('[data-modal]').forEach((btn) => {
    modalObj = new ModalObj(btn);
})



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

finds('[data-dropdown]').forEach((btn) => {
    dropdownObj = new DropdownObj(btn);
    dropdownObjs.push(dropdownObj);
})

bdy.addEventListener('click', hideDropdown);
function hideDropdown(e){
    if (!e.target.closest('[data-dropdown]') && !e.target.closest('.dropdown')) {
        finds('.dropdown').forEach((dd) => {
            dd.classList.remove('show');
        })
    }
}

window.addEventListener('resize', (e) => {
    let dd = find('.dropdown.show');
    if (dd == null) return;

    let ddObj = dropdownObjs.find((obj_) => {
        return obj_.dropdownDiv === dd;
    })
    if (ddObj == null) return;

    ddObj.positionDropdown();
})



class TabObj{
    constructor(btn) {
        this.tabElem = document.getElementById(btn.dataset.tab);
        this.btn = btn;
        btn.addEventListener('click', this.showTab.bind(this))
    }
    showTab(e){
        let tabContainer = this.tabElem.parentElement;
        if (this.tabElem.classList.contains('active_tab')) return;
        if (e.target.closest('.tab_dead_zone')) return;

        list_(tabContainer.children).forEach((elem) => {
            if (this.tabElem === elem) return;
            let elemBtn = find(`[data-tab = "${elem.id}"]`);
            elemBtn.setAttribute('tabindex', '-1');
            elemBtn.ariaSelected = false
            elem.classList.remove('active_tab');
            elemBtn.classList.remove('active_tab_btn');
        })
        this.tabElem.classList.add('active_tab');
        this.btn.classList.add('active_tab_btn');
        this.btn.ariaSelected = true;
        this.btn.setAttribute('tabindex', '0');
    }
}

finds('[data-tab]').forEach((btn) => {
    tabObj = new TabObj(btn);
})



class Tab2Obj{
    constructor(btn){
        this.sameTabBtns = finds(`[data-tab2 = ${btn.dataset.tab2}]`);
        this.tabElem = document.getElementById(btn.dataset.tab2);
        this.tabsHolder = this.tabElem.parentElement;
        btn.addEventListener('click', this.showTab.bind(this));
    }
    showTab(e){
        if (this.tabElem.classList.contains('active_tab2')) return;

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

finds('[data-tab2]').forEach((btn) => {
    tab2Obj = new Tab2Obj(btn);
})



class FloatObj{
    constructor(floatElem){
        this.floatElem = floatElem;
        let closeBtn = document.createElement('button');
        closeBtn.classList.add('icon_btn');
        closeBtn.innerHTML = '<i class="ri-close-large-line"></i>';
        closeBtn.addEventListener('click', this.hideFloat.bind(this));
        floatElem.append(closeBtn);
        this.floatContainer = document.createElement('aside');
        this.floatContainer.classList.add('float_container');
        this.floatContainer.append(floatElem);
        document.body.append(this.floatContainer);

        let floatRemoveTimeout;
        this.floatRemoveTimeout = floatRemoveTimeout;
        this.showFloatEvent = new CustomEvent('showFloat', {bubbles: true, cancelable: true, detail: {float_elem: floatElem }});
        bdy.addEventListener('keyup', this.hideFloatWithEscape.bind(this));
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

finds('[data-float]').forEach((float) => {
    floatObj = new FloatObj(float);
})