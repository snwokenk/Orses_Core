# Orses_Core

Orses Core Program for use in supporting Orses' Network MarketPlace And Blockchain
Those wishing to run this program, will be able to participate in validating blockchain
messages, validating marketplace messages, competing to create new blocks and overall acting
as administrators of the network


## Getting Started

Orses Core runs on python programming language and users must have **Python 3.6 or greater**.
Also, while any OS can be used. Ubuntu Linux is recommended

It is recommended you get python through anaconda. 
Anaconda python package can be downloaded with this link:
[Ananconda](https://www.anaconda.com/download/)

once Anaconda is installed. You can create an environment using:

`conda create --name myenv`

"myenv" can be changed to whatever name you desire

### Installing

To install you must first download or clone repository.

To download scroll up and click the green button that says "Clone or download"
Then click "Download zip" on the dropdown

Move the downloaded project to your preferred folder and unzip.

open the project folder and right click in it. You see an "open in terminal" option.
Click this to open a terminal within this folder.

Once terminal is open activate your conda environment using

`source activate myenv`

"myenv" should be the name of you gave your conda environment
Once it is activated

install any python module requirements using:

`pip install -r requirements.txt`

you might have to install as a super user using:
`'sudo pip install -r requirements.txt'`

### Running the program

Once all requirements are installed, you can run the program with this command:

`python start_node.py`

This will run the code in a sandbox network, between you and a virtual node called 'v1'
To run with more virtual nodes use "python start_node.py --sandbox (no_nodes)". for example:

`python start_node.py --sandbox 2`

Will run program in a sandbox network with 2 other nodes. 
It is recommended that to run with only 2 or less

To run a live network use:

`python start_node.py --live`


##### Testing

Using the Orses Client found in [Here](https://github.com/snwokenk/Orses_Client), and simultaneously
running this program. One can test how the network would react to a transaction or message 

##### Example

First run the program `python start_node.py`

### Built With

* [Twisted](https://github.com/twisted/twisted)
* [Pycryptodome](https://github.com/Legrandin/pycryptodome)



### Authors

* Samuel Nwokenkwo  [Snwokenk](https://github.com/snwokenk)


### Licence

This project is licensed under the MIT License.  
Read the [License](https://github.com/snwokenk/Orses_Core/blob/master/LICENSE)












 
