

// CHANGING ICON AFTER TOGGLING DETAILS
function changeDetailIcon(e){
    let iElem = find('[data-toggle-icon]', e.currentTarget);
    if (iElem === null ) return;

    if (iElem.className.startsWith('ri-arrow') && iElem.className.endsWith('s-line')) {
        if (iElem.className.includes('-up-') ){
            iElem.className = iElem.className.replace('up', 'down');
        } else {
            iElem.className = iElem.className.replace('down', 'up');
        }
    }
}
finds('summary[data-toggle-icon]').forEach((sum) => {
    sum.addEventListener('click', changeDetailIcon );
})

// DONT TOGGLE DETAILS EXCEPT BUTTON IS CLICKED
finds('summary').forEach((sum) => {
    sum.addEventListener('click', (e) => {
        if (!e.target.closest('.summary_toggle_btn')) {
            e.preventDefault();
        }
    })
})

// CLOSE DETAILS AFTER CLICKING THE TABS
function closeDetailAfterClickingTab(e){
    if (e.target.closest('.mobile_tab') || e.target.closest('.mobile_users_options')) {
        e.currentTarget.open = false;
    }
}
find('.menu_details').addEventListener('click', closeDetailAfterClickingTab);

// CLEAR INPUT WHEN CHECKBOX IS UNCHECKED
document.getElementById('minimumOddsCb')?.addEventListener('change', (e) => {
    if (e.currentTarget.checked){
        find('.min_odds_input').value = '';
    }
})


// UPDATE MODAL INFO AFTER OPENING
function updateDuelForm(e){
    let modal_container = e.detail.modal_container;
    let other_username;

    if (e.currentTarget.closest('.friends')){
        let user = e.target.closest('.friend');
        other_username = find('.friend_username', user).textContent;
        find('.their_code p', modal_container).textContent = other_username;
    } 
    else if (e.currentTarget.closest('#duels')) {
        let duel = e.target.closest('.duel');
        other_username = find('.duel_username', duel).textContent;
        find('.username_input', modal_container).value = other_username;
    }
}
function restoreDuelForm(e){
    let modal_container = e.detail.modal_container;
    if (e.currentTarget.closest('.friends')){
        find('.their_code p', modal_container).textContent = '';
    } 
    else if (e.currentTarget.closest('#duels')) {
        find('.username_input', modal_container).value = '';
    }
}

finds('.friends').forEach((elem) => {
    elem.addEventListener('showModal', updateDuelForm);
    elem.addEventListener('hideModal', restoreDuelForm);
})
find('#duels').addEventListener('showModal', updateDuelForm)
find('#duels').addEventListener('hideModal', restoreDuelForm);