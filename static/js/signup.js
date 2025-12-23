const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const fullNameRegex = /^[A-Za-z]+(?:-[A-Za-z]+)*(?:\s+[A-Za-z]+(?:-[A-Za-z]+)*)*$/;
const usernameRegex = /^(?!.*__)[A-Za-z][A-Za-z0-9_$@!#%&*-]{2,19}$/;
const passwordRegex = /^(?=.*[0-9]).{8,}$/;

let page1 = find('[data-page = "1"]');
let page2 = find('[data-page = "2"]');
let page3 = find('[data-page = "3"]');
let page4 = find('[data-page = "4"]');
let prevBtn = find('.prev_btn');
let nextBtn = find('.next_btn');
let activePage = find('.active_page');
let fnInput = find('input[name = "fname"]');
let emInput = find('input[name = "email"]');
pwdInput = find('input[name = "pwd"]');
pwdInput2 = find('input[name = "pwd2"]');
let usernameInput = find('input[name = "username"]');
let reviewCheckbox = find('.review input');
submitBtn = find('input[type = "submit"');

fnInput.regexObj = [fullNameRegex, 'Full Name must not contain any number or symbol'];
emInput.regexObj = [emailRegex, 'Invalid Email'];
pwdInput.regexObj = [passwordRegex, 'Password must contain a minimum of 8 characters and at least a number'];
usernameInput.regexObj = [usernameRegex, 'Invalid Username. Ensure it meets the guidelines'];

// ALL PAGES ARE NOT VALIDATED BY DEFAULT
finds('[data-page]').forEach((pg) => {
    pg.validated = false;
})


// COUNTRIES AND TEAMS 
data = {
    'country': { output: 'p.country_output', func: selectCountry},
    'team': { output: 'p.team_output', func: selectTeam}
};
function fillList(arr, container, type_){
    arr = list_(arr);
    container.innerHTML = '';
    let active_value = find( data[type_]['output'] )?.textContent;
    arr.forEach((item) => {
        let li = document.createElement('li');
        li.innerHTML = item;
        li.role = 'option'
        li.ariaSelected = false;
        li.tabIndex = 0;
        if (active_value != '' && active_value == item){
            li.classList.add('active');
            li.ariaSelected = true;
        }
        li.addEventListener('click', data[type_]['func']);
        li.addEventListener('keydown', selectWithKeyboard);
        container?.append(li);
    })
}

function selectCountry(e){
    activeItem = find('.active', e.currentTarget.closest('ul'));
    activeItem?.classList.remove('active');
    if (activeItem) activeItem.ariaSelected = false;

    e.currentTarget.classList.add('active');
    e.currentTarget.ariaSelected = true;
    find('p.country_output').textContent = e.currentTarget.textContent
    document.getElementById('nationality').value = e.currentTarget.textContent;
    showErrorMessage(page2, '');
}
function selectTeam(e){
    activeItem = find('.active', e.currentTarget.closest('ul'));
    activeItem?.classList.remove('active');
    if (activeItem) activeItem.ariaSelected = false;

    e.currentTarget.classList.add('active');
    e.currentTarget.ariaSelected = true;
    find('p.team_output').textContent = e.currentTarget.textContent
    document.getElementById('favTeam').value = e.currentTarget.textContent;
}

fillList(countries, find('.country_list'), 'country');
fillList(teams, find('.team_list'), 'team');

// SEARCH FUNCTION
find('.search_countries').addEventListener('input', (e) => {
    results = countries.filter((country) => {
        return country.toLowerCase().includes(e.currentTarget.value.toLowerCase());
    })
    fillList(results, find('.country_list'), 'country');
})

find('.search_teams').addEventListener('input', (e) => {
    results = teams.filter((team) => {
        return team.toLowerCase().includes(e.currentTarget.value.toLowerCase());
    })
    fillList(results, find('.team_list'), 'team');
})


// TOGGLE HIDDEN DETAIL
finds('.detail_toggler').forEach((btn) => {
    btn.addEventListener('click', (e) => {
        let detailDiv = btn.closest('div');
        let detail = find('.form_field_detail', detailDiv)
        detail.hidden = !detail.hidden;
    })
})

function handleNextPrevBtns(activePage){
    prevBtn.classList.toggle('hidden', activePage.dataset.page == 1);
    nextBtn.classList.toggle('hidden', activePage.dataset.page == 4);
}

find(`[data-bar = "${activePage.dataset.page}"`).classList.add('valid');
function updateActivityBars(activePage){
    let barNo = +activePage.dataset.page;
    for (let i = 1; i <= 4; i++){
        let bar = find(`[data-bar = "${i}"]`);
        if (i <= barNo) bar.classList.add('valid');
        else bar.classList.remove('valid');
    }
}
function transferActiveStatus(formerActive, newActive){
    formerActive.classList.remove('active_page');
    newActive.classList.add('active_page')
}
handleNextPrevBtns(activePage)

// NAVIGATING TO THE NEXT PAGE
prevBtn.addEventListener('click', (e) => {
    activePage = find('.active_page');
    let pageNo = +activePage.dataset.page;
    if (pageNo == 1) return;
    
    let prevPage = find(`[data-page = "${pageNo - 1}"]`);
    transferActiveStatus(activePage, prevPage);
    updateActivityBars(prevPage);
    handleNextPrevBtns(prevPage);
    
    e.preventDefault();
    
    if (prevPage.validated === true){
        showErrorMessage(prevPage, '');
    } else{
        showErrorMessage(prevPage, 'Form is not filled correctly')
    }
})
nextBtn.addEventListener('click', (e) => {
    activePage = find('.active_page');
    let pageNo = +activePage.dataset.page;
    if (pageNo == 4) return;

    if (activePage.validated === false){
        showErrorMessage(activePage, 'Form is not filled correctly');
    }
    else {
        let nextPage = find(`[data-page = "${pageNo + 1}"]`);
        transferActiveStatus(activePage, nextPage);
        updateActivityBars(nextPage);
        handleNextPrevBtns(nextPage);
    }

    e.preventDefault();
})


function emptyInput(input){
    if (input.value.trim() === '') return true;
    else return false;
}

function validateCheckbox(cbInput){
    error = '';
    if (!cbInput.checked) {
        error = 'Please tick the checkbox before submitting the form';
    } 
    return error;
}
function validateRadio(radInputs){
    error = '';
    let emptyRadio = radInputs.some((inp) => inp.checked);
    if (emptyRadio === false) {
        error = 'Pick an option';
    }
    return error;
}
function validateTextInputs(inputs){
    error = '';

    inputs.forEach((input) => {
        if (emptyInput(input)){
            error = `Fill all required fields`;
        } 
        else if (input.regexObj !== undefined) {
            [regex_, errMsg] = input.regexObj;
            if (!regex_.test(input.value.trim())) {
                error = errMsg;
            };
        }
        else if (input.name.includes('pwd')) {
            if (pwdInput2.value !== '' && (pwdInput.value.trim() !== pwdInput2.value.trim())) {
                error = 'Passwords do not match';
            }
        }
    })

    return error 
}

function showErrorMessage(page, errorMsg){
    errContainer = find('.form_error_txt small', page);
    if (errorMsg !== ''){
        errContainer.textContent = errorMsg;
        nextBtn.disabled = true;
        page.validated = false;
    } else {
        errContainer.textContent = '';
        nextBtn.disabled = false;    
        page.validated = true;
    }
}

function validatePage1and2(page){
    errContainer = find('.form_error_txt small', page)
    page.addEventListener('input', (e) => {
        error = validateTextInputs(finds('input[data-required]', page))
        showErrorMessage(page, error)
    })
}
function validatePage3(page){
    errContainer = find('.form_error_txt small', page)
    page.addEventListener('change', (e) => {
        error = validateRadio(finds('input[name="reason"]', page))
        showErrorMessage(page, error)
    })
}
function validatePage4(page){
    errContainer = find('.form_error_txt small', page)
    page.addEventListener('input', (e) => {
        inputError = validateTextInputs(finds('input[data-required]', page))
        cbError = validateCheckbox(reviewCheckbox)
        error = cbError || inputError;
        showErrorMessage(page, error);
    })
}

// VALIDATION FOR THE FORMS AND PREVENTING SUBMIT EVENT
validatePage1and2(page1);
validatePage1and2(page2);
validatePage3(page3);
validatePage4(page4);

submitBtn.addEventListener('click', (e) => {
    allValid = finds('[data-page]').every((pg) => pg.validated )
    if (!allValid) {
        e.preventDefault()
        find('.form_error_txt small', page4).textContent = 'Form is not filled correctly. Go through every page to correct any mistakes'
    };
})