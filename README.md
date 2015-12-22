# DeployApp
Deployment Tool.

## PreRequsite
- Repositories should be on gitlab (for now).
- on deployment servers there should be command which handles all deployment process.
- The command must take 3 args <code>deployment_branch</code> <code>username</code> <code>password</code>.

## Installment
### Linux
If <code>kivy</code> already installed, can be switched to other part;
```bash
$> sudo add-apt-repository ppa:kivy-team/kivy
$> sudo apt-get update
$> sudo apt-get install python-kivy
```
```bash
$> mkdir deploymentApp
$> cd deploymentApp
$> git clone https://github.com/RedXBeard/deployapp.git
$> cd deployapp
$> pip install -r requirements
```
To run, in cloned dir,
```bash
$> python main.py
```
### MacOS
Come up soon...
