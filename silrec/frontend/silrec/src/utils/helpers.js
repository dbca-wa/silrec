import currency from 'currency.js';
import { constants } from '@/utils/hooks';
export default {
    // Handle fetch get and post requests by stringifying JSON input and returning a JSON object
    fetchWrapper: async function (url, method, data) {
        let parsedMethod = null;
        if (method) {
            parsedMethod = method.trim().toUpperCase();
        }
        let response = null;
        if (!url) {
            throw 'You must specify a url';
        }
        if (arguments.length > 1) {
            if (!['POST', 'GET'].includes(parsedMethod)) {
                throw 'HTTP method must be GET or POST';
            }
            if (parsedMethod === 'POST' && !data) {
                throw 'POST method requires data argument';
            }
        }
        if (!parsedMethod || parsedMethod === 'GET') {
            try {
                const getResponse = await fetch(url);
                response = await getResponse.json();
            } catch (error) {
                console.error(error);
            }
        } else if (parsedMethod === 'POST') {
            try {
                const postResponse = await fetch(url, {
                    method: parsedMethod,
                    body: JSON.stringify(data),
                });
                response = await postResponse.json();
            } catch (error) {
                console.error(error);
            }
        }
        return response;
    },
    formatError: function (err) {
        let returnStr = '';
        // object {}
        if (
            typeof err.body === 'object' &&
            !Object.prototype.hasOwnProperty.call(err.body, 'length')
        ) {
            for (const key of Object.keys(err.body)) {
                returnStr += `${key}: ${err.body[key]} <br/>`;
            }
            // array
        } else if (typeof err.body === 'object') {
            returnStr = err.body[0];
            // string
        } else {
            returnStr = err.body;
        }
        return returnStr;
    },
    apiError: function (resp) {
        var error_str = '';
        if (resp.status === 400) {
            try {
                let obj = JSON.parse(resp.responseText);
                error_str = obj.non_field_errors[0].replace(/[[\]"]/g, '');
            } catch {
                error_str = resp.responseText.replace(/[[\]"]/g, '');
            }
        } else if (resp.status === 404) {
            error_str = 'The resource you are looking for does not exist.';
        } else {
            error_str = resp.responseText.replace(/[[\]"]/g, '');
        }
        return error_str;
    },
    apiVueResourceError: function (resp) {
        var error_str = '';
        var text = null;
        if (resp.status === 400) {
            if (Array.isArray(resp.body)) {
                text = resp.body[0];
            } else if (typeof resp.body == 'object') {
                text = resp.body;
            } else {
                text = resp.body;
            }

            if (typeof text == 'object') {
                if (
                    Object.prototype.hasOwnProperty.call(
                        text,
                        'non_field_errors'
                    )
                ) {
                    error_str = text.non_field_errors[0].replace(/[[\]"]/g, '');
                } else {
                    for (let key in text) {
                        error_str += key + ': ' + text[key] + '<br/>';
                    }
                }
            } else {
                error_str = text.replace(/[[\]"]/g, '');
                error_str = text.replace(/^['"](.*)['"]$/, '$1');
            }
        } else if (resp.status === 404) {
            error_str = 'The resource you are looking for does not exist.';
        }
        return error_str;
    },
    escapeHtml: function (htmlStr) {
        return htmlStr
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    },
    formatErrorV2: function (errors) {
        if (typeof errors === 'string') {
            return errors;
        }
        if (Array.isArray(errors)) {
            if (1 == errors.length) {
                return errors[0];
            } else {
                let errors_str = '';
                for (let i = 0; i < errors.length; i++) {
                    errors_str += errors[i] + '<br/>';
                }
                return errors_str;
            }
        }
        if (typeof errors === 'object') {
            if (1 == Object.keys(errors).length) {
                return Object.values(errors)[0];
            } else {
                let errors_str = '<ul class="list-group text-start">';
                for (const key of Object.keys(errors)) {
                    errors_str += `<li class="list-group-item"><span class="fw-bold">${key}:</span> ${module.exports.escapeHtml(
                        errors[key]
                    )}</li>`;
                }
                return errors_str + '</ul>';
            }
        }
    },
    goBack: function (vm) {
        vm.$router.go(window.history.back());
    },
    copyObject: function (obj) {
        return JSON.parse(JSON.stringify(obj));
    },
    getCookie: function (name) {
        var value = null;
        if (document.cookie && document.cookie !== '') {
            let cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                let cookie = cookies[i].trim();
                if (
                    cookie.substring(0, name.length + 1).trim() ===
                    name + '='
                ) {
                    value = decodeURIComponent(
                        cookie.substring(name.length + 1)
                    );
                    break;
                }
            }
        }
        return value;
    },
    namePopover: function ($, vmDataTable) {
        vmDataTable.on('mouseover', '.name_popover', function () {
            $(this).popover('show');
            $(this).on('mouseout', function () {
                $(this).popover('hide');
            });
        });
    },
    add_endpoint_json: function (string, addition) {
        let res = string.split('.json');
        let endpoint = res[0] + '/' + addition + '.json';
        endpoint = endpoint.replace('//', '/'); // Remove duplicated '/' just in case
        return endpoint;
    },
    add_endpoint_join: function (api_string, addition) {
        // assumes api_string has trailing forward slash '/' character required for POST
        let endpoint = api_string + addition;
        endpoint = endpoint.replace('//', '/'); // Remove duplicated '/' just in case
        // if the last character is not a forward slash then add one
        if (endpoint.slice(-1) != '/') {
            endpoint += '/';
        }
        return endpoint;
    },
    dtPopover: function (value, truncate_length = 30, trigger = 'hover') {
        var ellipsis = '...',
            truncated = _.truncate(value, {
                length: truncate_length,
                omission: ellipsis,
                separator: ' ',
            }),
            result = '<span>' + truncated + '</span>',
            popTemplate = _.template(
                '<a href="#" ' +
                    'role="button" ' +
                    'data-toggle="popover" ' +
                    'data-trigger="' +
                    trigger +
                    '" ' +
                    'data-placement="top auto"' +
                    'data-html="true" ' +
                    'data-content="<%= text %>" ' +
                    '>more</a>'
            );
        if (_.endsWith(truncated, ellipsis)) {
            result += popTemplate({
                text: value,
            });
        }
        return result;
    },
    dtPopoverCellFn: function (cell) {
        $(cell)
            .find('[data-toggle="popover"]')
            .popover()
            .on('click', function (e) {
                e.preventDefault();
                return true;
            });
    },
    processError: async function (err) {
        console.error(err);
        let errorText = '';
        if (err.body.non_field_errors) {
            // When non field errors raised
            for (let i = 0; i < err.body.non_field_errors.length; i++) {
                errorText += err.body.non_field_errors[i] + '<br />';
            }
        } else if (Array.isArray(err.body)) {
            // When serializers.ValidationError raised
            for (let i = 0; i < err.body.length; i++) {
                errorText += err.body[i] + '<br />';
            }
        } else {
            // When field errors raised
            for (let field_name in err.body) {
                if (
                    Object.prototype.hasOwnProperty.call(err.body, field_name)
                ) {
                    errorText += field_name + ':<br />';
                    for (let j = 0; j < err.body[field_name].length; j++) {
                        errorText += err.body[field_name][j] + '<br />';
                    }
                }
            }
        }
        await swal('Error', errorText, 'error');
    },
    post_and_redirect: function (url, postData) {
        /* http.post and ajax do not allow redirect from Django View (post method),
           this function allows redirect by mimicking a form submit.

           usage:  vm.post_and_redirect(vm.application_fee_url, {'csrfmiddlewaretoken' : vm.csrf_token});
        */
        var postFormStr = '<form method="POST" action="' + url + '">';

        for (let key in postData) {
            if (Object.prototype.hasOwnProperty.call(postData, key)) {
                postFormStr +=
                    '<input type="hidden" name="' +
                    key +
                    '" value="' +
                    postData[key] +
                    '">';
            }
        }
        postFormStr += '</form>';
        let formElement = $(postFormStr);
        $('body').append(formElement);
        $(formElement).submit();
    },
    enablePopovers: function () {
        let popoverTriggerList = [].slice.call(
            document.querySelectorAll('[data-bs-toggle="popover"]')
        );
        popoverTriggerList.map(function (popoverTriggerEl) {
            new bootstrap.Popover(popoverTriggerEl);
        });
    },
    parseFetchError: async function (response) {
        let errorString = '';
        let resData = '';
        try {
            resData = await response.json();
        } catch (error) {
            console.error(error);
            resData = response;
        }
        if (Array.isArray(resData)) {
            for (let i = 0; i < resData.length; i++) {
                errorString += resData[i] + '<br>';
            }
        } else {
            // Stringify obj
            errorString = JSON.stringify(resData);
        }
        console.error(errorString);
        return errorString;
    },
    getErrorStringFromResponseData(data) {
        let errorString = '';
        if (Array.isArray(data)) {
            for (let i = 0; i < data.length; i++) {
                errorString += data[i] + '<br>';
            }
        } else {
            errorString = JSON.stringify(data);
        }
        return errorString;
    },
    getFileIconClass: function (filepath, additional_class_names = []) {
        let ext = filepath.split('.').pop().toLowerCase();
        let classname = additional_class_names;

        if (['png', 'jpg', 'jpeg', 'bmp', 'tiff', 'tif'].includes(ext)) {
            classname.push('bi-file-image-fill');
        } else if (['pdf'].includes(ext)) {
            classname.push('bi-file-pdf-fill');
        } else if (['doc', 'docx'].includes(ext)) {
            classname.push('bi-file-word-fill');
        } else if (['xls', 'xlsx'].includes(ext)) {
            classname.push('bi-file-excel-fill');
        } else if (['txt', 'text'].includes(ext)) {
            classname.push('bi-file-text-fill');
        } else if (['rtf'].includes(ext)) {
            classname.push('bi-file-richtext-fill');
        } else if (['mp3', 'mp4'].includes(ext)) {
            classname.push('bi-file-play-fill');
        } else {
            classname.push('bi-file_fill');
        }

        return classname.join(' ');
    },
    formatABN: function (abn) {
        if (abn.length == 11) {
            return (
                abn.slice(0, 2) +
                ' ' +
                abn.slice(2, 5) +
                ' ' +
                abn.slice(5, 8) +
                ' ' +
                abn.slice(8, 11)
            );
        } else {
            return abn;
        }
    },
    formatACN: function (acn) {
        if (acn.length == 9) {
            return (
                acn.slice(0, 3) + ' ' + acn.slice(3, 6) + ' ' + acn.slice(6, 9)
            );
        } else {
            return acn;
        }
    },
    formatABNorACN: function (input) {
        if (input.length == 11) {
            return this.formatABN(input);
        } else if (input.length == 9) {
            return this.formatACN(input);
        } else {
            return input;
        }
    },
    validateABN: function (abn) {
        if (abn.length != 11) {
            return false;
        }
        let sum = 0;
        for (let i = 0; i < 11; i++) {
            let weight = 11 - i;
            sum += weight * abn[i];
        }
        return sum % 89 == 0;
    },
    validateACN: function (acn) {
        if (acn.length != 9) {
            return false;
        }
        let sum = 0;
        for (let i = 0; i < 8; i++) {
            let weight = 8 - i;
            sum += weight * acn[i];
        }
        return sum % 89 == 0;
    },
    isValidABNorACN: function (input) {
        if (input.length == 11) {
            return this.validateABN(input);
        } else if (input.length == 9) {
            return this.validateACN(input);
        } else {
            return false;
        }
    },
    formatDateForAPI: function (data, format = 'DD/MM/YYYY') {
        return data ? moment(data).format(format) : '';
    },
    calendarYearsIncluded: function (start_date, end_date) {
        const start = moment(start_date).year();
        const end = moment(end_date).year();
        return end - start + 1;
    },
    yearsInDateRange: function (start_date, end_date) {
        // Returns the number of years between two dates, rounded up
        const start = moment(start_date);
        const end = moment(end_date);
        return Math.ceil(end.diff(start, 'years', true));
    },
    datesOverlap: function (start_date1, end_date1, start_date2, end_date2) {
        const start1 = moment(start_date1);
        const end1 = moment(end_date1);
        const start2 = moment(start_date2);
        const end2 = moment(end_date2);
        return (
            (start1.isSameOrBefore(start2) && end1.isSameOrAfter(start2)) ||
            (start1.isSameOrBefore(end2) && end1.isSameOrAfter(end2)) ||
            (start1.isSameOrAfter(start2) && end1.isSameOrBefore(end2))
        );
    },
    financialYearsIncluded: function (start_date, end_date) {
        const financialYearsIncluded = [];
        const calendarYearsIncluded = this.calendarYearsIncluded(
            start_date,
            end_date
        );
        const startDate = moment(start_date);
        const endDate = moment(end_date);
        const startYear = moment(start_date).year() - 1;
        for (
            let i = startYear;
            i < startYear + calendarYearsIncluded + 1;
            i++
        ) {
            const startOfFinancialYear = moment(`${i}-07-01`);
            const endOfFinancialYear = moment(`${i + 1}-06-30`);
            if (
                this.datesOverlap(
                    startDate,
                    endDate,
                    startOfFinancialYear,
                    endOfFinancialYear
                )
            ) {
                financialYearsIncluded.push(`${i}-${i + 1}`);
            }
        }
        return financialYearsIncluded;
    },
    calendarYearHasPassed: function (year) {
        return new Date().year() > year;
    },
    financialYearHasStarted: function (financialYear) {
        const startOfFinancialYear = new Date(
            `${financialYear.split('-')[0]}-07-01`
        );
        return new Date() > startOfFinancialYear;
    },
    financialYearHasPassed: function (financialYear) {
        const endOfFinancialYear = new Date(
            `${financialYear.split('-')[1]}-06-30`
        );
        return new Date() > endOfFinancialYear;
    },
    sequentialYearHasPassed: function (startDate, year) {
        return moment(year).diff('years', moment(startDate).year()) > year;
    },
    getFinancialQuarterFromDate: function (date) {
        const month = moment(date).month();
        if (month < 3) {
            return 3;
        } else if (month < 6) {
            return 4;
        } else if (month < 9) {
            return 1;
        } else {
            return 2;
        }
    },
    getEndMonthForFinancialQuarter: function (financialQuarter) {
        return [8, 11, 2, 5][financialQuarter - 1];
    },
    financialQuarterHasPassed: function (financialYear, financialQuarter) {
        const month = this.getEndMonthForFinancialQuarter(financialQuarter);
        const year =
            financialQuarter > 2
                ? financialYear.split('-')[1]
                : financialYear.split('-')[0];
        const endOfFinancialQuarter = new Date(year, month + 1, 0);
        return new Date() > endOfFinancialQuarter;
    },
    monthHasPassed: function (year, month) {
        // Month is 1 indexed in this function
        const endOfMonth = new Date(year, month, 0);
        return new Date(new Date().toDateString()) > endOfMonth;
    },
    getStartMonthForFinancialQuarter: function (financialQuarter) {
        return [6, 9, 0, 3][financialQuarter - 1];
    },
    getFinancialYearFromDate: function (date) {
        const month = moment(date).month();
        const year = moment(date).year();
        if (month < 7) {
            return `${year - 1}-${year}`;
        } else {
            return `${year}-${year + 1}`;
        }
    },
    getFinancialQuarterLabel: function (quarter) {
        return ['JUL-SEP', 'OCT-DEC', 'JAN-MAR', 'APR-JUN'][quarter - 1];
    },
    getFinancialMonths: function (financialYear) {
        return [
            { year: financialYear.split('-')[0], month: 7, label: 'JUL' },
            { year: financialYear.split('-')[0], month: 8, label: 'AUG' },
            { year: financialYear.split('-')[0], month: 9, label: 'SEP' },
            { year: financialYear.split('-')[0], month: 10, label: 'OCT' },
            { year: financialYear.split('-')[0], month: 11, label: 'NOV' },
            { year: financialYear.split('-')[0], month: 12, label: 'DEC' },
            { year: financialYear.split('-')[1], month: 1, label: 'JAN' },
            { year: financialYear.split('-')[1], month: 2, label: 'FEB' },
            { year: financialYear.split('-')[1], month: 3, label: 'MAR' },
            { year: financialYear.split('-')[1], month: 4, label: 'APR' },
            { year: financialYear.split('-')[1], month: 5, label: 'MAY' },
            { year: financialYear.split('-')[1], month: 6, label: 'JUN' },
        ];
    },
    financialQuarterIncluded: function (
        startDate,
        endDate,
        financialYear,
        financialQuarter
    ) {
        let calendarYearApplicable = financialYear.split('-')[0];
        if (financialQuarter > 2) {
            calendarYearApplicable = financialYear.split('-')[1];
        }
        const financialQuarterStartMonth =
            this.getStartMonthForFinancialQuarter(financialQuarter);
        const financialQuarterEndMonth =
            this.getEndMonthForFinancialQuarter(financialQuarter);
        const startOfFinancialQuarter = moment().set({
            year: calendarYearApplicable,
            month: financialQuarterStartMonth,
            date: 1,
        });
        const endOfFinancialQuarter = moment()
            .set({
                year: calendarYearApplicable,
                month: financialQuarterEndMonth,
                date: 1,
            })
            .endOf('month')
            .set({
                hour: 0,
                minute: 0,
                second: 0,
                millisecond: 0,
            });

        return this.datesOverlap(
            startDate,
            endDate,
            startOfFinancialQuarter,
            endOfFinancialQuarter
        );
    },
    ordinalSuffixOf: function (i) {
        var j = i % 10,
            k = i % 100;
        if (j == 1 && k != 11) {
            return i + 'st';
        }
        if (j == 2 && k != 12) {
            return i + 'nd';
        }
        if (j == 3 && k != 13) {
            return i + 'rd';
        }
        return i + 'th';
    },
    yearsElapsedSinceStartDate: function (date) {
        return moment().diff(moment(date), 'years');
    },
    amountByRepetitionType: function (amount, repetitionTypeKey) {
        if (amount == null || amount == undefined) {
            throw 'amount must be defined';
        }
        if (repetitionTypeKey == null || repetitionTypeKey == undefined) {
            throw 'repetitionTypeKey must be defined';
        }
        if (currency(amount) == currency(0.0)) {
            return currency(0.0);
        }
        if (
            repetitionTypeKey == constants.INVOICING_REPETITON_TYPES.MONTHLY.ID
        ) {
            return currency(amount).divide(12);
        } else if (
            repetitionTypeKey ==
            constants.INVOICING_REPETITON_TYPES.QUARTERLY.ID
        ) {
            return currency(amount).divide(3);
        }
        return currency(amount);
    },
    /**
     * Function-parsable tagged template
     * @param {Array} strings Array of backtick (``) template literals / strings with a length equal to the number of substitutions (${}) plus one.
     * @param  {...any} keys Substitution (${}) keys in the template.
     * @returns A string with the substitutions applied.
     * @example const myTemplate = template`Hello ${'name'}, how are you?`;
     * myTemplate({ name: 'John' }); // Hello John, how are you?
     * @see https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Template_literals#tagged_templates
     */
    template: function (strings, ...keys) {
        return (...values) => {
            const dict = values[values.length - 1] || {};
            const result = [strings[0]];
            keys.forEach((key, i) => {
                const value = Number.isInteger(key) ? values[key] : dict[key];
                result.push(value, strings[i + 1]);
            });
            return result.join('');
        };
    },
};
