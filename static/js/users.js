

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
        let userId = user.dataset.user
        other_username = find('.friend_username', user).textContent;
        find('.their_code p', modal_container).textContent = other_username;
        find('.their_code input[type = hidden]', modal_container).value = userId;
    } 
    else if (e.currentTarget.closest('#duels')) {
        let duel = e.target.closest('.duel');
        let duel_username = find('.duelist:not(.you) .duel_username', duel);
        let duel_id = duel_username.dataset.duel;
        let duel_min_odds = duel_username.dataset.minOdds
        find('.duel_id_input', modal_container).value = duel_id;

        if (duel_min_odds !== 'None') {
            find('.duel_min_odds', modal_container).textContent = `Minimum - ${duel_min_odds}`;
        }
    }
}
function restoreDuelForm(e){
    let modal_container = e.detail.modal_container;
    if (e.currentTarget.closest('.friends')){
        find('.their_code p', modal_container).textContent = '';
        finds('input', modal_container).forEach((inp) => { inp.value = '' })
        find('#minimumOddsCb', modal_container).checked = false;
    } 
    else if (e.currentTarget.closest('#duels')) {
        find('.duel_id_input', modal_container).value = '';
        find('.duel_min_odds', modal_container).textContent = '';
    }
    find('.form_error_txt', modal_container).textContent = '';
}

finds('.friends').forEach((elem) => {
    elem.addEventListener('showModal', updateDuelForm);
    elem.addEventListener('hideModal', restoreDuelForm);
})
find('#duels').addEventListener('showModal', updateDuelForm)
find('#duels').addEventListener('hideModal', restoreDuelForm);


finds('.duels_filter_cb').forEach((label) => {
    let rad = find('input[type = radio]', label)
    label.addEventListener('click', (e) => {
        e.preventDefault();
        rad.checked = !rad.checked
    })
})

let pathIds = {
    'search-users': 'searchUser',
    'friend-requests': 'friendRequests',
    'duels': 'duels',
}

showPathTab(pathIds);