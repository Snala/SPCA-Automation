function printCookies() {
	return chrome.cookies.getAll({domain: "clinichq.com"})
}


//var callback = function() {
//  setTimeout(printCookies("from callback:"), 10000);
//};
//setTimeout(printCookies("not from callback:"), 10000);



async function postData(url = '', data = {}) {
  // Default options are marked with *

	let cookie_string;
	printCookies().then(function(response) {
		for (const item in response){
			if(cookie_string == null){
				cookie_string = `${response[item]['name']}=${response[item]['value']}; `;
			}
			else{
				cookie_string += `${response[item]['name']}=${response[item]['value']}; `;
			}
			cookie_string = cookie_string.slice(0, -2)
		}
		console.log(cookie_string)
	}, function(error){
		console.error("Failed!", error)
	})

  return fetch(url, {
    method: 'POST', // *GET, POST, PUT, DELETE, etc.
    mode: 'cors', // no-cors, *cors, same-origin
    cache: 'no-cache', // *default, no-cache, reload, force-cache, only-if-cached
    credentials: 'same-origin', // include, *same-origin, omit
    headers: {
		'Content-Type': 'application/json',
		'Cookie': cookie_string,
    },
    redirect: 'follow', // manual, *follow, error
    referrerPolicy: 'unsafe-url', // no-referrer, *no-referrer-when-downgrade, origin, origin-when-cross-origin, same-origin, strict-origin, strict-origin-when-cross-origin, unsafe-url
    body: JSON.stringify(data) // body data type must match "Content-Type" header
  }).then((response)=>response.json()).then((responseJson)=>{return responseJson});
}

document.getElementById('appointment').addEventListener("keypress", function(event) {
  // If the user presses the "Enter" key on the keyboard
  if (event.key === "Enter") {
    // Cancel the default action, if needed
    //event.preventDefault();
    // Trigger the button element with a click
    document.getElementById("submit").click();
  }
});

document.getElementById('submit').onclick = function() {
	var appointment = document.getElementById('appointment').value;
	var regex = /^[0-9]{8,9}$/;
	if(appointment.match(regex))
	{
		document.getElementById('appointment').value = "";
		chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
			var tab = tabs[0];
			async function caller() {
				const returned_data = await postData('https://clinichq.com/api/checkout/appointment/{}/checkin'.replace("{}", appointment));
				setTimeout(() => {}, 200);
				console.log(returned_data);
			}
			setTimeout(caller(), 1000)
			chrome.tabs.update(tab.id, {url: 'https://clinichq.com/checkout/#appointment/{}/details'.replace("{}", appointment)});
		});
	}
	else if (appointment == "")
	{
		chrome.tabs.query({active: true, currentWindow: true}, function(tabs){
			var tab = tabs[0];
			chrome.tabs.update(tab.id, {url: 'https://clinichq.com/account/login'});
		});
	}
	// document.getElementById('appointment').value = "";
    //chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
    //    var tab = tabs[0];
    //    chrome.tabs.update(tab.id, {url: 'https://clinichq.com/checkout/#appointment/{}/details'.replace("{}", appointment)});
    //});
};

