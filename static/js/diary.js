let selectLogicObj;
let headingAnimation = find('.heading_animation');
let filterEntriesModal = document.getElementById('filterEntriesModal');

let pathIds = {
    'entries': 'entriesTab',
    'create_entries': 'createEntryTab',
}
showPathTab(pathIds, 'entries');

headingAnimation.style.setProperty('--pos-x', `${Math.random() * 100}%`);
headingAnimation.style.setProperty('--pos-y', `${Math.random() * 100}%`);


function revertSelectMode(e){
    if (find('.entries_list') == null) return;
    let selectBtn = document.getElementById('selectBtn');
    let deleteSelectedBtn = document.getElementById('deleteSelectedBtn');

    selectBtn.innerHTML = 'Select <i class="ri-checkbox-line"></i>';
    deleteSelectedBtn.disabled = true;
    
    finds('.checkbox_container').forEach((container) => {
        container.classList.remove('show');
        container.previousElementSibling.classList.remove('checked');
        find('input', container).checked = false;
    })
}
find('#deleteEntriesModal')?.addEventListener('hx_close_modal', revertSelectMode);

function clearInputOnResetBtn(e){
    if (!e.target.closest('#filterFormResetBtn')) return;

    finds('.filter_input', e.currentTarget).forEach((inp) => { 
        inp.value = '';
    })
    find('input[type = checkbox]').checked = false;
}
filterEntriesModal.addEventListener('click', clearInputOnResetBtn);




// helper buttons config
function disableBtnWhenTabIsHidden(e){
    if (find('.entries_tab[aria-selected = true]') !== null) {
        finds('.helper_btns button').forEach((btn) => {
            btn.disabled = false;
        })
    } else{
        finds('.helper_btns button').forEach((btn) => {
            btn.disabled = true;
        })
    }
}
find('.tab_btns_holder').addEventListener('click', disableBtnWhenTabIsHidden)


function toggleFilterDirection(e){
    let iElem = find('i', e.currentTarget);
    let hiddenInput = find('input[type = "hidden"]', e.currentTarget.parentElement);
    if (iElem.className.includes('-up-')) {
        iElem.className = iElem.className.replace('-up-', '-down-');
        hiddenInput.value = 'lte';
        
    } else if (iElem.className.includes('-down-')) {
        iElem.className = iElem.className.replace('-down-', '-up-');
        hiddenInput.value = 'gte';  
    }
}
finds('.filter_input_grp button').forEach((btn) => {
    btn.addEventListener('click', toggleFilterDirection)
})




class SelectLogic{
    constructor(){
        this.selectBtn = document.getElementById('selectBtn')
        this.deleteSelectedBtn = document.getElementById('deleteSelectedBtn');

        finds('summary').forEach((sum) => {
            sum.addEventListener('click', this.changeDetailIcon.bind(this) );
        })

        this.selectBtn?.addEventListener('click', this.selectCheckboxes.bind(this));
        this.selectBtn?.addEventListener('click', this.updateSelectedCount.bind(this));

        finds('input[name = "deleted_item"]').forEach((cb) => {
            cb.addEventListener('click', this.highlightEntries.bind(this));
            cb.addEventListener('click', this.updateSelectedCount.bind(this));
        })

        find('.entries_list')?.addEventListener('showModal', (e) => {
            let modal = e.detail.modal_container;
            let modalBtn = e.detail.modal_btn;
            find('.heading_text', modal).textContent = 'Delete This Entry?';
            find('input', modal).value = modalBtn.dataset.entryId;
        })
        this.deleteSelectedBtn?.addEventListener('showModal', (e) => {
            let modal = e.detail.modal_container;
            let heading_text;
            let checkedNo = finds('input[name = "deleted_item"]:checked').length;
            
            if (checkedNo === 0) return;
            if (checkedNo === 1) heading_text = `Delete 1 Entry?`;
            else heading_text = `Delete ${checkedNo} Entries?`;

            find('.heading_text', modal).textContent = heading_text;
            find('input', modal).value = this.gatherCheckedInputsIds();
        })

        find('.entries_list')?.addEventListener('hideModal', this.hideModalListener.bind(this));
        this.deleteSelectedBtn?.addEventListener('hideModal', this.hideModalListener.bind(this));

    }

    changeDetailIcon(e){
        let iElem = find('[data-toggle-icon]', e.currentTarget);
        if (iElem === null || ( e.target.closest('.entry_delete_btn') )){
            return;
        }
        if (iElem.className.startsWith('ri-arrow') && iElem.className.endsWith('s-line')) {
            if (iElem.className.includes('-up-') ){
                iElem.className = iElem.className.replace('up', 'down');
            } else {
                iElem.className = iElem.className.replace('down', 'up');
            }
        }
    }

    selectCheckboxes(e){
        let cbsShowed = finds('.checkbox_container').every((container) => container.classList.contains('show'));

        if (cbsShowed){
            this.selectBtn.innerHTML = 'Select <i class="ri-checkbox-line"></i>';
            this.deleteSelectedBtn.disabled = true;
            
            finds('.checkbox_container').forEach((container) => {
                container.classList.remove('show');
                container.previousElementSibling.classList.remove('checked');
                find('input', container).checked = false;
            })
        } 
        else{
            this.selectBtn.innerHTML = 'Cancel <i class="ri-close-large-line"></i>';
            this.deleteSelectedBtn.disabled = false;

            finds('.checkbox_container').forEach((container) => {
                container.classList.add('show');
            })
        }
    }

    highlightEntries(e) {
        let cb = e.currentTarget;
        let entryDetails = e.currentTarget.parentElement.previousElementSibling;
        if (entryDetails instanceof HTMLDetailsElement) {
            entryDetails.classList.toggle('checked', cb.checked);
        }
    }
    updateSelectedCount(e){
        let checkedNo = finds('input[name = "deleted_item"]:checked').length;
        if (checkedNo === 0){
            find('span', this.deleteSelectedBtn).innerHTML = '';
            this.deleteSelectedBtn.disabled = true;
        } else{
            find('span', this.deleteSelectedBtn).innerHTML = `(${checkedNo})`;
            this.deleteSelectedBtn.disabled = false;
        }
    }

    gatherCheckedInputsIds(){
        let entryIds = finds('input[name = "deleted_item"]:checked').map((cb) => cb.dataset.entryId);
        return entryIds.join(',');
    }
    hideModalListener(e){
        let modal = e.detail.modal_container;
        find('input', modal).value = '';
    }    

}

selectLogicObj = new SelectLogic();



// INIT DROPDOWNS AFTER HTMX
bdy.addEventListener('hx_init_components', function(e) {
    if (!e.target.closest('.float_container')){
        initEntriesDropdowns();
        initEntriesModal();

        if (!bdy.contains(selectLogicObj.selectBtn)){
            selectLogicObj = new SelectLogic();
        }
    }
})

function initEntriesDropdowns(){
    dropdownObjs = dropdownObjs.filter((dd) => bdy.contains(dd.btn));
    
    finds('.entry [data-dropdown]').forEach((btn) => {
        dropdownObj = new DropdownObj(btn);
        dropdownObjs.push(dropdownObj);
    })
}

function initEntriesModal(){
    modalBtns = modalBtns.filter((btn) => bdy.contains(btn));
    finds('.entries [data-modal]').forEach((btn) => {
        if (!modalBtns.includes(btn)) {
            modalObj = new ModalObj(btn);
            modalBtns.push(modalObj.btn);
        }
    })
}