# Takina
A simple multipurpose bot for Discord.
For a list of features and other information please visit: https://orangc.xyz/takina.

## installation
Using the Dockerfile or Nix.

## TODO
- add autoroles / join roles
- replace aiohttp with requests where i can
- (long term) add a web dashboard for managing settings 
- better permissions system .. perhaps limit commands to the use app commands permission
- make every module where takina performs an action include the command executor in its reason
- levelling module
- make avatar fetch user IDs too and fix the error when it cant fetch a user
- make modules that don't support threads, support threads/forums: starboard(?), gh(?), and channels module.. also (?)
- make every command have it's own error embed responses, instead of using the global error handling

## License
[Here.](./LICENSE)