let selectBtn = document.getElementById('selectBtn')
let deleteSelectedBtn = document.getElementById('deleteSelectedBtn');
let deleteAllEntriesBtn = document.getElementById('deleteAllEntries');

// CHANGING ICON AFTER TOGGLING DETAILS
function changeDetailIcon(e){
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
finds('summary').forEach((sum) => {
    sum.addEventListener('click', changeDetailIcon );
})


// ACCORDION BEHAVIOUR.
// function closeOtherDetails(e){
//     let openDetail = find('.entry details[open]');
//     if (openDetail === null) return;

//     if (openDetail !== e.target.closest('details')) {
//         openDetail.open = false;
//     }
// }
// finds('.entry_slip').forEach((det) => {
//     det.addEventListener('click', closeOtherDetails);
// })


// select logic
function selectCheckboxes(e){
    let cbsShowed = finds('.checkbox_container').every((container) => container.classList.contains('show'));

    if (cbsShowed){
        selectBtn.innerHTML = 'Select <i class="ri-checkbox-line"></i>';
        deleteSelectedBtn.disabled = true;
        
        finds('.checkbox_container').forEach((container) => {
            container.classList.remove('show');
            container.previousElementSibling.classList.remove('checked');
            find('input', container).checked = false;
        })
    } 
    else{
        selectBtn.innerHTML = 'Cancel <i class="ri-close-large-line"></i>';
        deleteSelectedBtn.disabled = false;

        finds('.checkbox_container').forEach((container) => {
            container.classList.add('show');
        })
    }
}
selectBtn.addEventListener('click', selectCheckboxes)
selectBtn.addEventListener('click', updateSelectedCount)

// highlighting logic
function highlightEntries(e) {
    let cb = e.currentTarget;
    let entryDetails = e.currentTarget.parentElement.previousElementSibling;
    if (entryDetails instanceof HTMLDetailsElement) {
        entryDetails.classList.toggle('checked', cb.checked);
    }
}

function updateSelectedCount(e){
    let checkedNo = finds('input[name = "deleted_item"]:checked').length;
    if (checkedNo === 0){
        find('span', deleteSelectedBtn).innerHTML = '';
        deleteSelectedBtn.disabled = true;
    } else{
        find('span', deleteSelectedBtn).innerHTML = `(${checkedNo})`;
        deleteSelectedBtn.disabled = false;
    }
}

finds('input[name = "deleted_item"]').forEach((cb) => {
    cb.addEventListener('click', highlightEntries);
    cb.addEventListener('click', updateSelectedCount);
})


// helper buttons config
function disableBtnWhenTabIsHidden(e){
    if (find('.entries_tab.active_tab_btn') !== null) {
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


// Delete modals handling
function gatherCheckedInputsIds(){
    let entryIds = finds('input[name = "deleted_item"]:checked').map((cb) => cb.dataset.entryId);
    return entryIds.join(' || ');
}
function hideModalListener(e){
    let modal = e.detail.modal_container;
    find('input', modal).value = '';
}    

find('.entries_list').addEventListener('showModal', (e) => {
    let modal = e.detail.modal_container;
    let modalBtn = e.detail.modal_btn;
    find('.heading_text', modal).textContent = 'Delete This Entry?';
    find('input', modal).value = modalBtn.dataset.entryId;
})
deleteSelectedBtn.addEventListener('showModal', (e) => {
    let modal = e.detail.modal_container;
    let heading_text;
    let checkedNo = finds('input[name = "deleted_item"]:checked').length;
    
    if (checkedNo === 0) return;
    if (checkedNo === 1) heading_text = `Delete 1 Entry?`;
    else heading_text = `Delete ${checkedNo} Entries?`;

    find('.heading_text', modal).textContent = heading_text;
    find('input', modal).value = gatherCheckedInputsIds();
})

find('.entries_list').addEventListener('hideModal', hideModalListener);
deleteSelectedBtn.addEventListener('hideModal', hideModalListener);


function toggleFilterDirection(e){
    let iElem = find('i', e.currentTarget);
    let hiddenInput = find('input[type = "hidden"]', e.currentTarget.parentElement);
    if (iElem.className.includes('-up-')) {
        iElem.className = iElem.className.replace('-up-', '-down-');
        hiddenInput.value = 'down';
        
    } else if (iElem.className.includes('-down-')) {
        iElem.className = iElem.className.replace('-down-', '-up-');
        hiddenInput.value = 'up';  
    }
}
finds('.filter_input_grp button').forEach((btn) => {
    btn.addEventListener('click', toggleFilterDirection)
})