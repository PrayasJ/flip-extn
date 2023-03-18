const sendURL = document.getElementById('sub-button');
const listingBtn = document.getElementById('listings')
console.log(sendURL)

listingBtn.addEventListener( 'click', () => {
    window.open('http://localhost:8000/listings','_blank')
})
sendURL.addEventListener( 'click', () => {
	chrome.tabs.query({currentWindow: true, active: true}, async function(tabs){
        let body = JSON.stringify(
            {
                tab: tabs[0].url,
                vertical: document.getElementById('vertical').value
            }
        )
        let resp = await fetch('http://localhost:8000/', {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
              },
              body
        })
        window.close()
        // const req = new XMLHttpRequest()
        // const baseUrl = "http://localhost:5000/"
        // const urlParams = body
        // req.open("POST", baseUrl, true)
        // req.setRequestHeader("Content-type", "application/json")
        // req.send(urlParams)
        // req.onreadystatechange = function() { // Call a function when the state changes.
        //     if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
        //         console.log("Got response 200!");
        //     }
        // }
    });
} );