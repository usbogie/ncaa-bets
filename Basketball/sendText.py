from twilio.rest import TwilioRestClient

def sendText(body):
    accountSID = 'AC38fea5a3add1fb8dc2b3110457eb9ce5'
    authToken = '95225502aabaea96493635aeae8dae1a'
    twilioCli = TwilioRestClient(accountSID, authToken)
    myTwilioNumber = '+14159657083'
    myCellPhone = '+14157177149'
    message = twilioCli.messages.create(body='{}'.format(body), from_=myTwilioNumber, to=myCellPhone)
